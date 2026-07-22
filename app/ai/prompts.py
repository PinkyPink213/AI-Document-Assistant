from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import PromptTemplate
def build_rag_prompt():
    return ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an AI assistant.

Answer ONLY from the provided context.

If the answer cannot be found,
say you don't know.

Context

{context}
"""
        ),

        (
            "human",
            "{question}"
        )

    ]
)
    
def build_multi_query_prompt():
    return PromptTemplate(
        input_variables=["question"],
        template="""
    You are an AI assistant.

    Generate 5 different search queries for the following question.
    Each query should capture a different perspective.

    Question:
    {question}
    """
    
    ) 

def build_agent_prompt():
    return  """
            You are a helpful PDF assistant.

            Guidelines:
            - Use tools whenever document information is required.
            - Never guess filenames or page counts.
            - If a tool returns no data, explain it politely.
            """