from app.ai import get_vectorstore, build_multi_query_prompt ,get_llm, get_qdrant_client, get_embeddings
from langchain_classic.retrievers import MultiQueryRetriever

def retrieve_documents(question:str):
    client = get_qdrant_client()
    embeddings = get_embeddings()
    vector_store = get_vectorstore(client,embeddings)
    retriever = vector_store.as_retriever(
        search_kwargs={"k":5}
    )
   
   
    multi_query_retriever = MultiQueryRetriever.from_llm(
        retriever=retriever,
        llm=get_llm(),
        prompt=build_multi_query_prompt(),
    )
    
    docs = multi_query_retriever.invoke(question)

    context = "\n\n".join(
        doc.page_content
        for doc in docs
    )
    
    return context
    
# Top 5 Chunks