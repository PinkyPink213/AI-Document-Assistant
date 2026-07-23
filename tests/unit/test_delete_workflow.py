import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from app.ai import delete_workflow
from app.ai.delete_workflow import build_delete_document_workflow
from app.services.agent_service import extract_delete_filename


def test_extracts_pdf_from_explicit_delete_request():
    assert (
        extract_delete_filename("Delete timelen2.pdf from this conversation")
        == "timelen2.pdf"
    )
    assert extract_delete_filename('ลบ "annual report.pdf"') == "annual report.pdf"
    assert extract_delete_filename("Summarize timelen2.pdf") is None


@pytest.mark.asyncio
async def test_delete_workflow_interrupts_then_deletes_after_approval(monkeypatch):
    calls = []

    class FakeDeleteTool:
        def invoke(self, arguments):
            calls.append(arguments)
            return 'The document "timelen2.pdf" was successfully deleted from this conversation.'

    monkeypatch.setattr(delete_workflow, "delete_document", FakeDeleteTool())
    workflow = build_delete_document_workflow(InMemorySaver())
    config = {
        "configurable": {
            "thread_id": "conversation:8:document-deletion",
        }
    }

    pending = await workflow.ainvoke(
        {"conversation_id": 8, "filename": "timelen2.pdf"},
        config=config,
    )

    assert pending["__interrupt__"][0].value["action_requests"][0]["args"] == {
        "filename": "timelen2.pdf",
        "conversation_id": 8,
    }
    assert calls == []

    completed = await workflow.ainvoke(
        Command(resume={"decision": "approve"}),
        config=config,
    )

    assert calls == [{"filename": "timelen2.pdf", "conversation_id": 8}]
    assert (
        completed["result"]
        == 'The document "timelen2.pdf" was successfully deleted from this conversation.'
    )


@pytest.mark.asyncio
async def test_delete_workflow_does_not_delete_after_rejection(monkeypatch):
    class FakeDeleteTool:
        def invoke(self, arguments):
            raise AssertionError("Delete must not run after rejection")

    monkeypatch.setattr(delete_workflow, "delete_document", FakeDeleteTool())
    workflow = build_delete_document_workflow(InMemorySaver())
    config = {
        "configurable": {
            "thread_id": "conversation:9:document-deletion",
        }
    }
    await workflow.ainvoke(
        {"conversation_id": 9, "filename": "keep.pdf"},
        config=config,
    )

    completed = await workflow.ainvoke(
        Command(resume={"decision": "reject"}),
        config=config,
    )

    assert completed["result"] == "Deletion cancelled. 'keep.pdf' was not removed."
