from langchain_core.documents import Document

from app.ai.retriever import (
    build_document_filter,
    format_cited_context,
    resolve_mentioned_filename,
)
from app.ai.citations import (
    citation_coverage,
    ensure_academic_citations,
    ensure_source_citations,
    has_document_citation,
    reject_deleted_document_citations,
)
from app.services.agent_service import (
    AgentService,
    ConversationNotFoundError,
    get_pending_interrupt,
)
from app.services.chat_routing import is_academic_search_request
import pytest


def test_routes_named_file_to_filename_filter():
    filename = resolve_mentioned_filename(
        "What is the main result in TIMELEN2.PDF?",
        ["annual-report.pdf", "timelen2.pdf"],
    )
    retrieval_filter = build_document_filter(4, filename)

    assert filename == "timelen2.pdf"
    assert [condition.key for condition in retrieval_filter.must] == [
        "metadata.conversation_id",
        "metadata.filename",
    ]
    assert retrieval_filter.must[1].match.value == "timelen2.pdf"


def test_routes_filename_stem_to_filename_filter():
    assert (
        resolve_mentioned_filename(
            "Summarize the conclusions from annual-report",
            ["annual-report.pdf"],
        )
        == "annual-report.pdf"
    )


def test_routes_unknown_file_question_to_conversation_filter():
    filename = resolve_mentioned_filename(
        "What risks are discussed across our documents?",
        ["annual-report.pdf", "timelen2.pdf"],
    )
    retrieval_filter = build_document_filter(4, filename)

    assert filename is None
    assert len(retrieval_filter.must) == 1
    assert retrieval_filter.must[0].key == "metadata.conversation_id"
    assert retrieval_filter.must[0].match.value == 4


def test_retrieval_filter_allows_only_active_postgres_documents():
    retrieval_filter = build_document_filter(
        4,
        active_document_ids=["active-vector-id"],
    )

    assert [condition.key for condition in retrieval_filter.must] == [
        "metadata.conversation_id",
        "metadata.document_id",
    ]
    assert retrieval_filter.must[1].match.any == ["active-vector-id"]


def test_formats_retrieved_chunks_with_source_markers():
    context = format_cited_context(
        [
            Document(
                page_content="Revenue increased by 12%.",
                metadata={"filename": "annual-report.pdf", "page": 14},
            )
        ]
    )

    assert context == (
        "[SOURCE 1: annual-report.pdf, page 14]\nRevenue increased by 12%."
    )


def test_does_not_append_a_separate_sources_section():
    class ToolMessage:
        type = "tool"
        content = "[SOURCE 1: annual-report.pdf, page 14]\nEvidence"

    answer = ensure_source_citations("Revenue increased.", [ToolMessage()])

    assert answer == "Revenue increased."
    assert "Sources" not in answer


def test_does_not_duplicate_grouped_inline_page_citations():
    class ToolMessage:
        type = "tool"
        content = "\n".join(
            [
                "[SOURCE 1: timelen2.pdf, page 1]",
                "[SOURCE 2: timelen2.pdf, page 2]",
                "[SOURCE 3: timelen2.pdf, page 5]",
                "[SOURCE 4: timelen2.pdf, page 19]",
            ]
        )

    response = (
        "The report describes the architecture "
        "[timelen2.pdf, pages 1-2, 5, 7, 9, 19]."
    )

    assert ensure_source_citations(response, [ToolMessage()]) == response
    assert has_document_citation(response, "timelen2.pdf", "2")
    assert has_document_citation(response, "timelen2.pdf", "19")


def test_keeps_inline_citation_without_appending_missing_candidates():
    class ToolMessage:
        type = "tool"
        content = "\n".join(
            [
                "[SOURCE 1: report.pdf, page 1]",
                "[SOURCE 2: report.pdf, page 3]",
            ]
        )

    answer = ensure_source_citations(
        "Summary [report.pdf, page 1].",
        [ToolMessage()],
    )

    assert answer == "Summary [report.pdf, page 1]."
    assert "Sources" not in answer


def test_removes_model_generated_sources_section_from_grounded_answer():
    class ToolMessage:
        type = "tool"
        content = "[SOURCE 1: attention.pdf, page 1]\nEvidence"

    response = (
        "Transformers use self-attention [attention.pdf, p. 1].\n\n"
        "**Sources**\n"
        "- [attention.pdf, p. 1]"
    )

    answer = ensure_source_citations(response, [ToolMessage()])

    assert answer == "Transformers use self-attention [attention.pdf, p. 1]."


def test_omits_sources_when_documents_do_not_contain_the_answer():
    class ToolMessage:
        type = "tool"
        content = "\n".join(
            [
                "[SOURCE 1: attention.pdf, page 1]",
                "[SOURCE 2: attention.pdf, page 15]",
            ]
        )

    response = (
        "The current uploaded documents do not contain information about "
        "what TimeLens2 is.\n\n"
        "**Sources**\n"
        "- [attention.pdf, p. 1]\n"
        "- [attention.pdf, p. 15]"
    )

    answer = ensure_source_citations(response, [ToolMessage()])

    assert answer.endswith("what TimeLens2 is.")
    assert "Sources" not in answer
    assert "attention.pdf" not in answer


def test_calculates_document_and_academic_citation_coverage():
    class ToolMessage:
        type = "tool"
        content = "\n".join(
            [
                "[SOURCE 1: annual-report.pdf, page 14]",
                "[SOURCE 2: risks.pdf, page 3]",
                "[ACADEMIC SOURCE 1: Forecasting paper | "
                "https://doi.org/10.1000/example]",
            ]
        )

    coverage = citation_coverage(
        "See [annual-report.pdf, p. 14] and "
        "[Forecasting paper](https://doi.org/10.1000/example).",
        [ToolMessage()],
    )

    assert coverage == {
        "citation_source_count": 3,
        "citation_count": 2,
        "citation_coverage": 2 / 3,
    }


def test_finds_pending_human_interrupt_in_agent_state():
    class Interrupt:
        value = {"action_requests": [{"name": "delete_document"}]}

    class Task:
        interrupts = (Interrupt(),)

    class State:
        tasks = (Task(),)

    assert get_pending_interrupt(State()) == {
        "action_requests": [{"name": "delete_document"}]
    }


def test_does_not_reuse_academic_sources_from_an_older_turn():
    class Message:
        def __init__(self, message_type, content):
            self.type = message_type
            self.content = content

    messages = [
        Message(
            "tool",
            "[ACADEMIC SOURCE 1: Old paper | https://doi.org/10.1000/old]",
        ),
        Message("human", "Delete my PDF"),
        Message("ai", "Approval is required."),
    ]

    assert (
        ensure_academic_citations("Approval is required.", messages)
        == "Approval is required."
    )


def test_rejects_answer_citing_a_deleted_document():
    response = (
        "Transformers use attention mechanisms "
        "[attention.pdf, pages 1, 4]."
    )

    result = reject_deleted_document_citations(
        response,
        ["timelen2.pdf"],
    )

    assert "could not find supporting information" in result
    assert "attention.pdf" not in result


def test_keeps_answer_citing_an_active_document():
    response = "The model uses temporal grounding [timelen2.pdf, p. 2]."

    assert (
        reject_deleted_document_citations(response, ["timelen2.pdf"])
        == response
    )


def test_agent_service_rejects_a_deleted_conversation():
    class MissingConversationRepository:
        def get_by_id(self, conversation_id):
            return None

    service = AgentService(
        message_repository=None,
        agent=None,
        delete_document_workflow=None,
        conversation_repository=MissingConversationRepository(),
    )

    with pytest.raises(
        ConversationNotFoundError,
        match="Conversation 11 no longer exists",
    ):
        service.ensure_conversation_exists(11)


def test_detects_explicit_external_paper_search():
    assert is_academic_search_request(
        "Could you search the TimeLens2 paper for me?"
    )
    assert is_academic_search_request(
        "Suggest three publications about transformer forecasting"
    )
    assert not is_academic_search_request(
        "What does attention.pdf say about transformers?"
    )
