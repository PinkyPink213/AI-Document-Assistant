from langchain_core.documents import Document

from app.ai.retriever import (
    build_document_filter,
    format_cited_context,
    resolve_mentioned_filename,
)
from app.services.agent_service import (
    citation_coverage,
    ensure_academic_citations,
    ensure_source_citations,
    get_pending_interrupt,
)


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


def test_appends_sources_when_model_omits_citations():
    class ToolMessage:
        type = "tool"
        content = "[SOURCE 1: annual-report.pdf, page 14]\nEvidence"

    answer = ensure_source_citations("Revenue increased.", [ToolMessage()])

    assert answer.endswith("**Sources**\n- [annual-report.pdf, p. 14]")


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
