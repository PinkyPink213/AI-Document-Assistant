from app.ai.retriever import build_document_filter, resolve_mentioned_filename


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
