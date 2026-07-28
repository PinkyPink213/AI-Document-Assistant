import logging
import time

from langgraph.types import Command
from langsmith import trace

from app.ai.academic_search import search_academic_papers
from app.ai.citations import (
    ACADEMIC_SOURCE_PATTERN,
    citation_coverage,
    ensure_academic_citations,
    ensure_source_citations,
    reject_deleted_document_citations,
)
from app.ai.retriever import list_conversation_filenames
from app.core.observability import (
    LangSmithMetricsCallback,
    request_id_context,
)
from app.repositories import ChatMessageRepository, ConversationRepository
from app.services.chat_routing import (
    academic_search_query,
    extract_delete_filename,
    is_academic_search_request,
    requested_paper_limit,
)

logger = logging.getLogger(__name__)


class ConversationNotFoundError(LookupError):
    pass


def delete_workflow_thread_id(conversation_id: int) -> str:
    return f"conversation:{conversation_id}:document-deletion"


def format_direct_academic_response(tool_result: str, query: str) -> str:
    """Render MCP results without allowing document-history hallucinations."""
    normalized = tool_result.casefold()
    if (
        "no academic papers matched" in normalized
        or "none included a usable source url" in normalized
    ):
        return f'No academic papers were found for "{query}".'
    if "temporarily unavailable" in normalized:
        return (
            "The external academic search service is temporarily unavailable. "
            "Please try again shortly."
        )

    matches = ACADEMIC_SOURCE_PATTERN.findall(tool_result)
    if not matches:
        return f'No academic papers were found for "{query}".'

    items = [
        f"{index}. [{title.strip()}]({url.strip()})"
        for index, (title, url) in enumerate(matches, start=1)
    ]
    return "Here are the academic papers I found:\n\n" + "\n\n".join(items)


def get_pending_interrupt(state) -> dict | None:
    for task in getattr(state, "tasks", ()):
        for interrupt in getattr(task, "interrupts", ()):
            value = getattr(interrupt, "value", None)
            if isinstance(value, dict):
                return value
    return None


class AgentService:
    """
    Service responsible for interacting with the LangGraph Agent.
    """

    def __init__(
        self,
        message_repository: ChatMessageRepository,
        agent,
        delete_document_workflow,
        conversation_repository: ConversationRepository,
    ):
        self.agent = agent
        self.delete_document_workflow = delete_document_workflow
        self.message_repository = message_repository
        self.conversation_repository = conversation_repository

    def ensure_conversation_exists(self, conversation_id: int) -> None:
        if self.conversation_repository.get_by_id(conversation_id) is None:
            raise ConversationNotFoundError(
                f"Conversation {conversation_id} no longer exists."
            )

    def list_messages(self, conversation_id: int):
        self.ensure_conversation_exists(conversation_id)
        return self.message_repository.list_by_conversation(conversation_id)

    @staticmethod
    def _build_agent_config(
        conversation_id: int,
        callback: LangSmithMetricsCallback,
        trace_metadata: dict[str, str],
    ) -> dict:
        return {
            "configurable": {
                "thread_id": str(conversation_id),
            },
            "callbacks": [callback],
            "tags": ["document-assistant", "chat"],
            "metadata": trace_metadata,
        }

    @staticmethod
    def _build_delete_config(conversation_id: int) -> dict:
        return {
            "configurable": {
                "thread_id": delete_workflow_thread_id(conversation_id),
            }
        }

    async def _get_pending_approval(
        self,
        agent_config: dict,
        delete_config: dict,
    ) -> tuple[dict | None, object]:
        """Return an existing approval before accepting another user action."""
        delete_state = await self.delete_document_workflow.aget_state(
            delete_config
        )
        pending_delete = get_pending_interrupt(delete_state)
        if pending_delete:
            return pending_delete, None

        agent_state = await self.agent.aget_state(agent_config)
        pending_agent_action = get_pending_interrupt(agent_state)
        return pending_agent_action, agent_state

    async def _start_delete_workflow(
        self,
        conversation_id: int,
        filename: str,
        delete_config: dict,
    ) -> dict:
        result = await self.delete_document_workflow.ainvoke(
            {
                "conversation_id": conversation_id,
                "filename": filename,
            },
            config=delete_config,
        )
        interrupt_value = result["__interrupt__"][0].value
        logger.info(
            "Document deletion requires approval: conversation=%s filename=%s",
            conversation_id,
            filename,
        )
        return {
            "response": None,
            "interrupt": interrupt_value,
        }

    async def _run_direct_academic_search(
        self,
        conversation_id: int,
        question: str,
        external_query: str,
    ) -> dict:
        tool_result = await search_academic_papers.ainvoke(
            {
                "query": external_query,
                "conference_only": "conference" in question.casefold(),
                "limit": requested_paper_limit(question),
            }
        )
        response = format_direct_academic_response(
            str(tool_result),
            external_query,
        )
        self.message_repository.create(
            conversation_id,
            "assistant",
            response,
        )
        return {"response": response}

    @staticmethod
    def _build_input_messages(
        conversation_id: int,
        question: str,
        persisted_history: list,
        agent_state,
    ) -> list[dict[str, str]]:
        checkpoint_messages = (
            agent_state.values.get("messages", {})
            if agent_state and agent_state.values
            else {}
        )
        active_filenames = list_conversation_filenames(conversation_id)
        active_files_text = (
            ", ".join(active_filenames) if active_filenames else "none"
        )
        academic_instruction = (
            "The user is explicitly requesting external academic paper search. "
            "You MUST call search_academic_papers; do not search uploaded documents."
            if is_academic_search_request(question)
            else ""
        )
        context_message = {
            "role": "system",
            "content": (
                f"The active conversation ID is {conversation_id}. "
                f"Currently uploaded PDFs: {active_files_text}. "
                "Only these filenames are active; files mentioned solely in "
                "earlier chat history may have been deleted. Use the current "
                "list for document tools. "
                f"{academic_instruction}"
            ),
        }
        current_question = {"role": "user", "content": question}

        # PostgreSQL restores visible chat history when a graph thread has no
        # checkpoint messages yet, without duplicating an existing graph history.
        if not checkpoint_messages and persisted_history:
            history_messages = [
                {"role": message.role, "content": message.content}
                for message in persisted_history
            ]
            return [context_message, *history_messages, current_question]

        return [context_message, current_question]

    async def _run_agent(
        self,
        conversation_id: int,
        input_messages: list[dict[str, str]],
        agent_config: dict,
        callback: LangSmithMetricsCallback,
        trace_metadata: dict[str, str],
    ) -> dict:
        started = time.perf_counter()
        with trace(
            "chat_request",
            run_type="chain",
            inputs={"question": input_messages[-1]["content"]},
            tags=["document-assistant", "chat"],
            metadata=trace_metadata,
        ) as run:
            result = await self.agent.ainvoke(
                {"messages": input_messages},
                config=agent_config,
                version="v2",
            )

            if result.interrupts:
                run.add_metadata({"human_approval_required": True})
                logger.info("Human approval required.")
                return {
                    "response": None,
                    "interrupt": result.interrupts[0].value,
                }

            response = result.value["messages"][-1].content
            response = ensure_source_citations(
                response,
                result.value["messages"],
            )
            response = ensure_academic_citations(
                response,
                result.value["messages"],
            )
            response = reject_deleted_document_citations(
                response,
                list_conversation_filenames(conversation_id),
            )
            coverage = citation_coverage(
                response,
                result.value["messages"],
            )
            run.add_metadata(
                {
                    **coverage,
                    "input_tokens": callback.input_tokens,
                    "output_tokens": callback.output_tokens,
                    "total_tokens": callback.total_tokens,
                    "llm_latency_ms": round(callback.llm_latency_ms, 2),
                    "cost_tracking": "langsmith_automatic",
                }
            )
            run.end(outputs={"response": response})

        self.message_repository.create(
            conversation_id,
            "assistant",
            response,
        )
        logger.info(
            "Agent response generated",
            extra={
                "event": "agent.completed",
                "agent_latency_ms": round(
                    (time.perf_counter() - started) * 1000,
                    2,
                ),
                "input_tokens": callback.input_tokens,
                "output_tokens": callback.output_tokens,
                "total_tokens": callback.total_tokens,
                "llm_latency_ms": round(callback.llm_latency_ms, 2),
                "cost_tracking": "langsmith_automatic",
                **coverage,
            },
        )
        return {"response": response}

    async def chat(
        self,
        conversation_id: int,
        question: str,
    ) -> dict:
        """Route a user message through the appropriate chat workflow."""
        self.ensure_conversation_exists(conversation_id)

        callback = LangSmithMetricsCallback()
        trace_metadata = {
            "request_id": request_id_context.get(),
            "conversation_id": str(conversation_id),
            "operation": "chat",
        }
        agent_config = self._build_agent_config(
            conversation_id,
            callback,
            trace_metadata,
        )
        delete_config = self._build_delete_config(conversation_id)
        logger.info("User question: %s", question)

        pending_approval, agent_state = await self._get_pending_approval(
            agent_config,
            delete_config,
        )
        if pending_approval:
            logger.info(
                "Conversation %s is awaiting a human decision.",
                conversation_id,
            )
            return {
                "response": None,
                "interrupt": pending_approval,
            }

        persisted_history = self.message_repository.list_by_conversation(
            conversation_id
        )
        self.message_repository.create(
            conversation_id,
            "user",
            question,
        )

        filename = extract_delete_filename(question)
        if filename:
            return await self._start_delete_workflow(
                conversation_id,
                filename,
                delete_config,
            )

        external_query = academic_search_query(question, persisted_history)
        if external_query:
            return await self._run_direct_academic_search(
                conversation_id,
                question,
                external_query,
            )

        input_messages = self._build_input_messages(
            conversation_id,
            question,
            persisted_history,
            agent_state,
        )
        return await self._run_agent(
            conversation_id,
            input_messages,
            agent_config,
            callback,
            trace_metadata,
        )

    async def resume(
        self,
        conversation_id: int,
        decision: str,
        message: str | None = None,
    ):
        """
        Resume an interrupted workflow.

        decision:
            approve
            reject
        """
        self.ensure_conversation_exists(conversation_id)
        thread_id = str(conversation_id)
        
        logger.info(
            "Resuming thread %s with decision '%s'",
            thread_id,
            decision,
        )

        delete_config = {
            "configurable": {
                "thread_id": delete_workflow_thread_id(conversation_id),
            }
        }
        delete_state = await self.delete_document_workflow.aget_state(
            delete_config
        )
        if get_pending_interrupt(delete_state):
            result = await self.delete_document_workflow.ainvoke(
                Command(
                    resume={
                        "decision": decision,
                        "message": message,
                    }
                ),
                config=delete_config,
            )
            response = result["result"]
            self.message_repository.create(
                conversation_id,
                "assistant",
                response,
            )
            return {
                "response": response,
                "interrupt": None,
            }

        payload = {
            "type": decision,
        }

        if message:
            payload["message"] = message

        result = await self.agent.ainvoke(
            Command(
                resume={
                    "decisions": [
                        payload,
                    ]
                }
            ),
            config={
                "configurable": {
                    "thread_id": thread_id,
                }
            },
            version="v2",
        )


        logger.info("Workflow resumed successfully.")

        response = result.value["messages"][-1].content
        self.message_repository.create(conversation_id, "assistant", response)

        return {
            "response": response,
            "interrupt": None,
        }
