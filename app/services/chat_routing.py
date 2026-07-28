import re


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
