from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_classic.retrievers import MultiQueryRetriever
from langchain_core.prompts import PromptTemplate

from qdrant_client import QdrantClient

from app.core.config  import settings

def get_embeddings():
    embeddings = OpenAIEmbeddings(
        model=settings.openai_embeddings_model,
        api_key=settings.openai_api_key,
    )
    return embeddings

def get_llm():
    llm = init_chat_model(
        model=settings.openai_chat_model,
        api_key=settings.openai_api_key,
        temperature=0,      
    )
    return llm

def get_vector_store():
    client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
    )

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=settings.qdrant_collection_name,
        embedding=get_embeddings()
    )
    return vector_store


def build_prompt():
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are a helpful AI assistant.

                Answer ONLY from the provided context.

                Context:
                {context}
                """,
            ),
            ("human","{question}")
        ]
    )
    
    return prompt

def retrieve_documents(question:str):
    
    retriever = get_vector_store().as_retriever(
        search_kwargs={"k":5}
    )
   
   
    QUERY_PROMPT = PromptTemplate(
        input_variables=["question"],
        template="""
    You are an AI assistant.

    Generate 5 different search queries for the following question.
    Each query should capture a different perspective.

    Question:
    {question}
    """
    ) 
    multi_query_retriever = MultiQueryRetriever.from_llm(
        retriever=retriever,
        llm=get_llm(),
        prompt=QUERY_PROMPT,
    )
    
    # queries = multi_query_retriever.generate_queries(
    #     question,
    #     run_manager=CallbackManagerForRetrieverRun.get_noop_manager(),
    # )

    # print("Generated Queries:")
    # for i, q in enumerate(queries, start=1):
    #     print(f"{i}. {q}")
    
    docs = multi_query_retriever.invoke(question)

    context = "\n\n".join(
        doc.page_content
        for doc in docs
    )
    
    return context

def ask(question: str):
    context = retrieve_documents(question)
    
    prompt = build_prompt()
    
    messages = prompt.invoke(
        {
            "context": context,
            "question": question,
        }
    )
    llm = get_llm()

    response = llm.invoke(messages)
    return response

if __name__ == "__main__":
    question ="What is Transformer?"
    response = ask(question)
    print(response.content)
    
#  python -m demo.rag_pipeline  