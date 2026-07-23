from typing import TypedDict

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from app.ai.tools import delete_document


class DeleteDocumentState(TypedDict, total=False):
    conversation_id: int
    filename: str
    decision: str
    result: str


def review_and_delete(state: DeleteDocumentState) -> DeleteDocumentState:
    filename = state["filename"]
    conversation_id = state["conversation_id"]
    review = interrupt(
        {
            "action_requests": [
                {
                    "name": "delete_document",
                    "args": {
                        "filename": filename,
                        "conversation_id": conversation_id,
                    },
                    "description": (
                        f"Delete '{filename}' from conversation {conversation_id}. "
                        "This removes its PostgreSQL metadata and Qdrant vectors."
                    ),
                }
            ],
            "review_configs": [
                {
                    "action_name": "delete_document",
                    "allowed_decisions": ["approve", "reject"],
                }
            ],
        }
    )
    decision = str(review.get("decision", "reject"))
    if decision != "approve":
        return {
            "decision": "reject",
            "result": f"Deletion cancelled. '{filename}' was not removed.",
        }

    result = delete_document.invoke(
        {
            "filename": filename,
            "conversation_id": conversation_id,
        }
    )
    return {
        "decision": "approve",
        "result": result,
    }


def build_delete_document_workflow(checkpointer: BaseCheckpointSaver):
    workflow = StateGraph(DeleteDocumentState)
    workflow.add_node("review_and_delete", review_and_delete)
    workflow.add_edge(START, "review_and_delete")
    workflow.add_edge("review_and_delete", END)
    return workflow.compile(checkpointer=checkpointer)
