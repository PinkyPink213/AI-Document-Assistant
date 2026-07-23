import asyncio
import json
import logging
import sys
from typing import Any, Literal

from langchain.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient


ACADEMIC_SERVER_NAME = "academic-search"
ACADEMIC_SEARCH_TOOL_NAME = "search_papers"
logger = logging.getLogger(__name__)


def _academic_client() -> MultiServerMCPClient:
    return MultiServerMCPClient(
        {
            ACADEMIC_SERVER_NAME: {
                "transport": "stdio",
                "command": sys.executable,
                "args": ["-m", "academic_search"],
            }
        },
        handle_tool_errors=True,
    )


def _decode_mcp_result(result: Any) -> dict[str, Any]:
    if isinstance(result, dict) and "papers" in result:
        return result

    if isinstance(result, list):
        text_parts = []
        for item in result:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(str(item.get("text", "")))
            elif hasattr(item, "text"):
                text_parts.append(str(item.text))
        if text_parts:
            decoded = json.loads("\n".join(text_parts))
            if isinstance(decoded, dict):
                return decoded

    if isinstance(result, str):
        decoded = json.loads(result)
        if isinstance(decoded, dict):
            return decoded

    raise ValueError("Academic search returned an unsupported response.")


def _paper_url(paper: dict[str, Any]) -> str | None:
    pdf = paper.get("openAccessPdf")
    if isinstance(pdf, dict) and pdf.get("url"):
        return str(pdf["url"])

    external_ids = paper.get("externalIds")
    if isinstance(external_ids, dict) and external_ids.get("DOI"):
        return f"https://doi.org/{external_ids['DOI']}"

    if paper.get("url"):
        return str(paper["url"])

    if paper.get("paperId"):
        return f"https://www.semanticscholar.org/paper/{paper['paperId']}"

    return None


def format_academic_results(payload: dict[str, Any]) -> str:
    papers = payload.get("papers")
    if not isinstance(papers, list) or not papers:
        return "No academic papers matched the requested topic and filters."

    formatted: list[str] = []
    for index, paper in enumerate(papers, start=1):
        if not isinstance(paper, dict):
            continue

        title = str(paper.get("title") or "Untitled paper").strip()
        url = _paper_url(paper)
        if not url:
            continue

        journal = paper.get("journal")
        if isinstance(journal, dict):
            venue = journal.get("name")
        else:
            venue = journal

        author_values = paper.get("authors") or []
        authors = [
            str(author.get("name") if isinstance(author, dict) else author)
            for author in author_values[:3]
        ]
        if len(author_values) > 3:
            authors.append("et al.")

        abstract = " ".join(str(paper.get("abstract") or "").split())
        if len(abstract) > 500:
            abstract = f"{abstract[:497].rstrip()}..."

        details = [
            f"[ACADEMIC SOURCE {index}: {title} | {url}]",
            f"Title: {title}",
            f"URL: {url}",
        ]
        if paper.get("year"):
            details.append(f"Year: {paper['year']}")
        if venue:
            details.append(f"Venue: {venue}")
        if authors:
            details.append(f"Authors: {', '.join(authors)}")
        if paper.get("citationCount") is not None:
            details.append(f"Citations: {paper['citationCount']}")
        if paper.get("publicationTypes"):
            details.append(
                f"Publication type: {', '.join(paper['publicationTypes'])}"
            )
        if abstract:
            details.append(f"Abstract excerpt: {abstract}")
        formatted.append("\n".join(details))

    if not formatted:
        return "Papers were found, but none included a usable source URL."

    return "\n\n".join(formatted)


@tool
async def search_academic_papers(
    query: str,
    conference_only: bool = False,
    year_min: int | None = None,
    year_max: int | None = None,
    limit: int = 5,
    provider: Literal[
        "semantic_scholar", "crossref", "openalex", "pubmed"
    ] = "semantic_scholar",
) -> str:
    """Search external scholarly databases for paper recommendations.

    Use only when the user asks to discover external papers, related work,
    literature, conference papers, or research recommendations. Do not use
    this tool to answer questions about PDFs uploaded to the conversation.
    Returns verified titles, URLs, metadata, and abstract excerpts.
    """
    safe_limit = max(1, min(limit, 8))
    try:
        async with asyncio.timeout(35):
            client = _academic_client()
            tools = await client.get_tools(server_name=ACADEMIC_SERVER_NAME)
            mcp_search = next(
                tool for tool in tools if tool.name == ACADEMIC_SEARCH_TOOL_NAME
            )
            result = await mcp_search.ainvoke(
                {
                    "query": query,
                    "limit": safe_limit,
                    "max_retrieval": max(50, safe_limit * 20),
                    "provider": provider,
                    "publication_types": (
                        "Conference" if conference_only else None
                    ),
                    "year_min": year_min,
                    "year_max": year_max,
                    "has_abstract": True,
                }
            )
            return format_academic_results(_decode_mcp_result(result))
    except Exception:
        logger.exception("Academic search MCP request failed")
        return (
            "Academic search is temporarily unavailable. Tell the user the "
            "external scholarly provider could not be reached and suggest retrying."
        )
