import json

import pytest

from app.ai import academic_search
from app.ai.academic_search import (
    _decode_mcp_result,
    format_academic_results,
    search_academic_papers,
)
from app.services.agent_service import ensure_academic_citations


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

    assert calls[0]["publication_types"] == "Conference"
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
