import json

import pytest

from app.ai import academic_search
from app.ai.academic_search import (
    _decode_mcp_result,
    format_academic_results,
    search_academic_papers,
)
from app.ai.citations import ensure_academic_citations
from app.services.agent_service import format_direct_academic_response
from app.services.chat_routing import academic_search_query


PAPER = {
    "paperId": "paper-123",
    "externalIds": {"DOI": "10.1000/example"},
    "title": "Transformers for Time Series Forecasting",
    "year": 2024,
    "citationCount": 12,
    "publicationTypes": ["Conference"],
    "journal": {"name": "International Forecasting Conference"},
    "authors": [{"name": "Ada Researcher"}],
    "abstract": "A transformer architecture for multivariate forecasting.",
}


def test_decodes_text_content_from_mcp():
    result = [{"type": "text", "text": json.dumps({"papers": [PAPER]})}]

    assert _decode_mcp_result(result)["papers"][0]["title"] == PAPER["title"]


def test_formats_academic_result_with_verified_url_and_metadata():
    result = format_academic_results({"papers": [PAPER]})

    assert f"Title: {PAPER['title']}" in result
    assert "URL: https://doi.org/10.1000/example" in result
    assert (
        "Required title link: "
        "[Transformers for Time Series Forecasting]"
        "(https://doi.org/10.1000/example)"
    ) in result
    assert "Venue: International Forecasting Conference" in result
    assert "Publication type: Conference" in result
    assert "[ACADEMIC SOURCE 1:" in result


def test_appends_academic_links_when_model_omits_them():
    class ToolMessage:
        type = "tool"
        content = (
            "[ACADEMIC SOURCE 1: Transformers for Time Series | "
            "https://doi.org/10.1000/example]"
        )

    answer = ensure_academic_citations(
        "This paper is relevant to forecasting.", [ToolMessage()]
    )

    assert answer.endswith(
        "**Paper links**\n"
        "- [Transformers for Time Series](https://doi.org/10.1000/example)"
    )


def test_appends_each_missing_academic_link():
    class ToolMessage:
        type = "tool"
        content = "\n".join(
            [
                "[ACADEMIC SOURCE 1: Linked paper | https://doi.org/10.1000/one]",
                "[ACADEMIC SOURCE 2: Missing paper | https://doi.org/10.1000/two]",
            ]
        )

    answer = ensure_academic_citations(
        "The first result is available at https://doi.org/10.1000/one.",
        [ToolMessage()],
    )

    assert "[Missing paper](https://doi.org/10.1000/two)" in answer
    assert answer.count("https://doi.org/10.1000/one") == 1


def test_moves_generic_paper_link_onto_its_title():
    class ToolMessage:
        type = "tool"
        content = (
            "[ACADEMIC SOURCE 1: Transformers for Time Series | "
            "https://doi.org/10.1000/example]"
        )

    answer = ensure_academic_citations(
        '"Transformers for Time Series" (2025). Useful summary. '
        "[Open paper](https://doi.org/10.1000/example)",
        [ToolMessage()],
    )

    assert (
        "[Transformers for Time Series](https://doi.org/10.1000/example)"
        in answer
    )
    assert "Open paper" not in answer


def test_formats_direct_mcp_results_as_clickable_titles_without_sources():
    result = "\n\n".join(
        [
            "[ACADEMIC SOURCE 1: TimeLens Research | "
            "https://doi.org/10.1000/one]\nTitle: TimeLens Research",
            "[ACADEMIC SOURCE 2: Video Temporal Grounding | "
            "https://doi.org/10.1000/two]\nTitle: Video Temporal Grounding",
        ]
    )

    answer = format_direct_academic_response(result, "TimeLens2")

    assert "[TimeLens Research](https://doi.org/10.1000/one)" in answer
    assert "[Video Temporal Grounding](https://doi.org/10.1000/two)" in answer
    assert "Sources" not in answer


def test_direct_mcp_no_results_has_no_sources():
    answer = format_direct_academic_response(
        "No academic papers matched the requested topic and filters.",
        "TimeLens2",
    )

    assert answer == 'No academic papers were found for "TimeLens2".'
    assert "Sources" not in answer


def test_resolves_academic_follow_up_from_previous_offer():
    class Message:
        def __init__(self, role, content):
            self.role = role
            self.content = content

    history = [
        Message("user", "What is TimeLens2?"),
        Message(
            "assistant",
            "The uploaded documents do not contain that information. "
            "I can find external academic papers about TimeLens2. "
            "Would you like me to do that?",
        ),
    ]

    assert academic_search_query("Could you find for me?", history) == "TimeLens2"


def test_extracts_topic_from_explicit_paper_search():
    assert (
        academic_search_query(
            "Could you search timelen2 paper for me?",
            [],
        )
        == "timelen2"
    )


@pytest.mark.asyncio
async def test_academic_tool_calls_mcp_with_conference_filter(monkeypatch):
    calls = []

    class FakeSearchTool:
        name = "search_papers"

        async def ainvoke(self, arguments):
            calls.append(arguments)
            return [{"type": "text", "text": json.dumps({"papers": [PAPER]})}]

    class FakeClient:
        async def get_tools(self, server_name):
            assert server_name == "academic-search"
            return [FakeSearchTool()]

    monkeypatch.setattr(academic_search, "_academic_client", FakeClient)

    result = await search_academic_papers.ainvoke(
        {
            "query": "transformers for time series",
            "conference_only": True,
            "limit": 3,
        }
    )

    assert calls[0]["provider"] == "crossref"
    assert calls[0]["publication_types"] == "proceedings-article"
    assert calls[0]["max_retrieval"] == 30
    assert calls[0]["limit"] == 3
    assert PAPER["title"] in result


@pytest.mark.asyncio
async def test_academic_tool_returns_recoverable_error(monkeypatch):
    class UnavailableClient:
        async def get_tools(self, server_name):
            raise ConnectionError("provider unavailable")

    monkeypatch.setattr(academic_search, "_academic_client", UnavailableClient)

    result = await search_academic_papers.ainvoke({"query": "time series"})

    assert "temporarily unavailable" in result
