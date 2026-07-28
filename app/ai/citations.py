import logging
import re


logger = logging.getLogger(__name__)

SOURCE_PATTERN = re.compile(
    r"\[SOURCE \d+:\s*([^,\]]+),\s*page\s*([^\]]+)\]",
    re.IGNORECASE,
)
ACADEMIC_SOURCE_PATTERN = re.compile(
    r"\[ACADEMIC SOURCE \d+:\s*(.*?)\s*\|\s*(https?://[^\]\s]+)\]",
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
    # Document citations must stay inline. Never render a duplicate trailing
    # Sources section, including one generated directly by the model.
    _ = messages
    response = SOURCES_SECTION_PATTERN.sub("", response).rstrip()
    normalized_response = " ".join(response.casefold().split())
    if any(pattern in normalized_response for pattern in NO_EVIDENCE_PATTERNS):
        return response
    return response


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
