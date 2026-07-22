from langchain.agents.middleware import HumanInTheLoopMiddleware


def get_human_in_the_loop():
    return HumanInTheLoopMiddleware(
        interrupt_on={
            "delete_document": {
                "allowed_decisions": [
                    "approve",
                    "reject",
                ]
            }
        }
    )