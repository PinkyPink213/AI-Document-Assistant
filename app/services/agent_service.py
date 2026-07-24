import logging
import re
import time

from langgraph.types import Command
from langsmith import trace

from app.ai.academic_search import search_academic_papers
from app.ai.retriever import list_conversation_filenames
from app.core.observability import (
    LangSmithMetricsCallback,
    request_id_context,
)
from app.repositories import ChatMessageRepository, ConversationRepository

logger = logging.getLogger(__name__)


SOURCE_PATTERN = re.compile(
    r"\[SOURCE \d+:\s*([^,\]]+),\s*page\s*([^\]]+)\]",
    re.IGNORECASE,
)
ACADEMIC_SOURCE_PATTERN = re.compile(
    r"\[ACADEMIC SOURCE \d+:\s*(.*?)\s*\|\s*(https?://[^\]\s]+)\]",
    re.IGNORECASE,
)
PDF_FILENAME_PATTERN = re.compile(
    r"""(?:"([^"]+\.pdf)"|'([^']+\.pdf)'|([^\s"'\\/]+\.pdf))""",
    re.IGNORECASE,
)
DELETE_KEYWORDS = ("delete", "remove", "ลบ")
ACADEMIC_SEARCH_PATTERN = re.compile(
    r"\b(?:find|search|suggest|recommend|discover)\b.*\b"
    r"(?:paper|papers|publication|publications|literature|research)\b"
    r"|\b(?:paper|papers|publication|publications|literature)\b.*\b"
    r"(?:find|search|suggest|recommend|discover)\b",
    re.IGNORECASE,
)
FINAL_DOCUMENT_CITATION_PATTERN = re.compile(
    r"\[([^\]\n]+\.pdf),\s*p(?:age|ages)?\.?\s*[^\]]+\]",
    re.IGNORECASE,
)
NO_CURRENT_DOCUMENT_INFORMATION = (
    "I could not find supporting information in the documents currently "
    "uploaded to this conversation. Please upload the relevant PDF or ask "
    "a question about one of the available documents."
)
NO_EVIDENCE_PATTERNS = (
    "do not contain information",
    "does not contain information",
    "did not find supporting information",
    "could not find supporting information",
    "couldn't find supporting information",
    "no supporting information was found",
    "no relevant content was found",
)
SOURCES_SECTION_PATTERN = re.compile(
    r"\n+\*{0,2}sources\*{0,2}\s*\n.*\Z",
    re.IGNORECASE | re.DOTALL,
)
ACADEMIC_FOLLOW_UP_PATTERN = re.compile(
    r"^\s*(?:yes|yes please|please do|sure|okay|ok|"
    r"could you (?:find|search)(?: it)? for me\??|"
    r"(?:find|search) for me\??)\s*$",
    re.IGNORECASE,
)
ACADEMIC_TOPIC_PATTERNS = (
    re.compile(
        r"\b(?:find|search|suggest|recommend|discover)\s+"
        r"(?:for me\s+)?(.+?)\s+(?:papers?|publications?)"
        r"(?:\s+for me)?(?:\s*[?.]|$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:papers?|publications?|literature|research)\s+"
        r"(?:about|on|related to)\s+(.+?)(?:[?.]|$)",
        re.IGNORECASE,
    ),
)


class ConversationNotFoundError(LookupError):
    pass


def delete_workflow_thread_id(conversation_id: int) -> str:
    return f"conversation:{conversation_id}:document-deletion"


def extract_delete_filename(question: str) -> str | None:
    normalized = question.casefold()
    if not any(keyword in normalized for keyword in DELETE_KEYWORDS):
        return None

    match = PDF_FILENAME_PATTERN.search(question)
    if not match:
        return None
    return next(value.strip() for value in match.groups() if value)


def is_academic_search_request(question: str) -> bool:
    return ACADEMIC_SEARCH_PATTERN.search(question) is not None


def academic_search_query(question: str, history: list) -> str | None:
    """Resolve explicit paper searches and affirmative academic follow-ups."""
    if is_academic_search_request(question):
        for pattern in ACADEMIC_TOPIC_PATTERNS:
            match = pattern.search(question)
            if match:
                return match.group(1).strip(" .?")
        return question.strip()

    if not ACADEMIC_FOLLOW_UP_PATTERN.match(question):
        return None

    last_assistant = next(
        (
            message.content
            for message in reversed(history)
            if message.role == "assistant"
        ),
        "",
    )
    if "external academic" not in last_assistant.casefold():
        return None

    offered_topic = re.search(
        r"(?:about|on)\s+([A-Za-z0-9][A-Za-z0-9_. -]*?)(?:[?.]|$)",
        last_assistant,
        re.IGNORECASE,
    )
    if offered_topic:
        return offered_topic.group(1).strip(" .?")

    previous_question = next(
        (
            message.content
            for message in reversed(history)
            if message.role == "user"
        ),
        "",
    )
    topic = re.sub(
        r"^\s*(?:what|who)\s+is\s+",
        "",
        previous_question,
        flags=re.IGNORECASE,
    )
    return topic.strip(" .?") or None


def requested_paper_limit(question: str, default: int = 3) -> int:
    match = re.search(r"\b([1-8])\s+(?:papers?|publications?)\b", question)
    return int(match.group(1)) if match else default


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


def current_turn_messages(messages: list) -> list:
    for index in range(len(messages) - 1, -1, -1):
        message = messages[index]
        message_type = getattr(message, "type", None)
        role = getattr(message, "role", None)
        if message_type == "human" or role == "user":
            return messages[index:]
    return messages


def has_document_citation(response: str, filename: str, page: str) -> bool:
    """Recognize individual and grouped page citations for one document."""
    citation_pattern = re.compile(
        rf"\[{re.escape(filename.strip())},\s*"
        rf"(?:p(?:age|ages)?\.?)\s*([^\]]+)\]",
        re.IGNORECASE,
    )
    requested_page = page.strip()
    if not requested_page.isdigit():
        return any(
            requested_page.casefold() in page_expression.casefold()
            for page_expression in citation_pattern.findall(response)
        )

    requested_number = int(requested_page)
    for page_expression in citation_pattern.findall(response):
        for start, end in re.findall(
            r"(\d+)(?:\s*[-–]\s*(\d+))?",
            page_expression,
        ):
            range_start = int(start)
            range_end = int(end or start)
            if min(range_start, range_end) <= requested_number <= max(
                range_start,
                range_end,
            ):
                return True
    return False


def ensure_source_citations(response: str, messages: list) -> str:
    normalized_response = " ".join(response.casefold().split())
    if any(pattern in normalized_response for pattern in NO_EVIDENCE_PATTERNS):
        return SOURCES_SECTION_PATTERN.sub("", response).rstrip()

    sources: list[tuple[str, str]] = []
    for message in current_turn_messages(messages):
        if getattr(message, "type", None) != "tool":
            continue
        content = str(getattr(message, "content", ""))
        for filename, page in SOURCE_PATTERN.findall(content):
            source = (filename.strip(), page.strip())
            if source not in sources:
                sources.append(source)

    if not sources:
        return response

    missing_sources = [
        (filename, page)
        for filename, page in sources
        if not has_document_citation(response, filename, page)
    ]
    if not missing_sources:
        return response

    source_list = "\n".join(
        f"- [{filename}, p. {page}]" for filename, page in missing_sources
    )
    return f"{response.rstrip()}\n\n**Sources**\n{source_list}"


def reject_deleted_document_citations(
    response: str,
    active_filenames: list[str],
) -> str:
    """Prevent an answer from relying on a PDF no longer present in PostgreSQL."""
    active = {filename.strip().casefold() for filename in active_filenames}
    cited = {
        filename.strip().casefold()
        for filename in FINAL_DOCUMENT_CITATION_PATTERN.findall(response)
    }
    if cited and not cited.issubset(active):
        logger.warning(
            "Rejected answer containing citations to inactive documents",
            extra={
                "event": "agent.stale_document_citation",
                "inactive_filenames": sorted(cited - active),
            },
        )
        return NO_CURRENT_DOCUMENT_INFORMATION
    return response


def ensure_academic_citations(response: str, messages: list) -> str:
    sources: list[tuple[str, str]] = []
    for message in current_turn_messages(messages):
        if getattr(message, "type", None) != "tool":
            continue
        content = str(getattr(message, "content", ""))
        for title, url in ACADEMIC_SOURCE_PATTERN.findall(content):
            source = (title.strip(), url.strip())
            if source not in sources:
                sources.append(source)

    if not sources:
        return response

    for title, url in sources:
        title_link = f"[{title}]({url})"
        if title_link in response:
            continue

        generic_link_pattern = re.compile(
            rf"\[(?:open\s+paper|read\s+more)\]\({re.escape(url)}\)",
            re.IGNORECASE,
        )
        response = generic_link_pattern.sub("", response)

        quoted_title_pattern = re.compile(
            rf'["“”]?{re.escape(title)}["“”]?',
            re.IGNORECASE,
        )
        if quoted_title_pattern.search(response):
            response = quoted_title_pattern.sub(title_link, response, count=1)

    missing_sources = [
        (title, url) for title, url in sources if url not in response
    ]
    if not missing_sources:
        return response

    source_list = "\n".join(
        f"- [{title}]({url})" for title, url in missing_sources
    )
    return f"{response.rstrip()}\n\n**Paper links**\n{source_list}"


def citation_coverage(response: str, messages: list) -> dict[str, float | int]:
    """Measure how many retrieved sources are represented in the final answer."""
    expected: set[str] = set()
    cited: set[str] = set()
    for message in current_turn_messages(messages):
        if getattr(message, "type", None) != "tool":
            continue
        content = str(getattr(message, "content", ""))
        for filename, page in SOURCE_PATTERN.findall(content):
            key = f"document:{filename.strip()}:{page.strip()}"
            expected.add(key)
            if has_document_citation(response, filename, page):
                cited.add(key)
        for title, url in ACADEMIC_SOURCE_PATTERN.findall(content):
            key = f"academic:{title.strip()}:{url.strip()}"
            expected.add(key)
            if url.strip() in response:
                cited.add(key)

    expected_count = len(expected)
    cited_count = len(cited)
    return {
        "citation_source_count": expected_count,
        "citation_count": cited_count,
        "citation_coverage": (
            cited_count / expected_count if expected_count else 1.0
        ),
    }


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

    async def chat(
        self,
        conversation_id: int,
        question: str, 
    ):
        """
        Send a user message to the agent.
        """
        self.ensure_conversation_exists(conversation_id)
        thread_id = str(conversation_id)
        callback = LangSmithMetricsCallback()
        trace_metadata = {
            "request_id": request_id_context.get(),
            "conversation_id": str(conversation_id),
            "operation": "chat",
        }
        config = {
            "configurable": {
                "thread_id": thread_id,
            },
            "callbacks": [callback],
            "tags": ["document-assistant", "chat"],
            "metadata": trace_metadata,
        }
        delete_config = {
            "configurable": {
                "thread_id": delete_workflow_thread_id(conversation_id),
            }
        }
        logger.info("User question: %s", question)
        delete_state = await self.delete_document_workflow.aget_state(
            delete_config
        )
        pending_delete = get_pending_interrupt(delete_state)
        if pending_delete:
            return {
                "response": None,
                "interrupt": pending_delete,
            }

        state = await self.agent.aget_state(config)
        pending_interrupt = get_pending_interrupt(state)
        if pending_interrupt:
            logger.info(
                "Thread %s is awaiting a human decision; returning its interrupt.",
                thread_id,
            )
            return {
                "response": None,
                "interrupt": pending_interrupt,
            }

        persisted_history = self.message_repository.list_by_conversation(conversation_id)
        self.message_repository.create(conversation_id, "user", question)

        filename = extract_delete_filename(question)
        if filename:
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

        external_query = academic_search_query(question, persisted_history)
        if external_query:
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
            return {
                "response": response,
            }

        checkpoint_messages = state.values.get("messages", {}) if state.values else {}
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
        input_messages = [context_message, {"role": "user", "content": question}]
        if not checkpoint_messages and persisted_history:
            input_messages = [context_message] + [
                {"role": message.role, "content": message.content}
                for message in persisted_history
            ] + [{"role": "user", "content": question}]

        started = time.perf_counter()
        with trace(
            "chat_request",
            run_type="chain",
            inputs={"question": question},
            tags=["document-assistant", "chat"],
            metadata=trace_metadata,
        ) as run:
            result = await self.agent.ainvoke(
                {
                    "messages": input_messages,
                },
                config=config,
                version="v2",
            )

            if result.interrupts:
                run.add_metadata({"human_approval_required": True})
                logger.info("Human approval required.")
                return {
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
        self.message_repository.create(conversation_id, "assistant", response)

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

        return {
            "response": response,
        }

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
