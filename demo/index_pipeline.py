from pathlib import Path
import uuid

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client.models import PayloadSchemaType
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.core.config  import settings

def load_pdf(filename: str) -> list[Document]:
    project_root = Path(__file__).resolve().parents[1]
    pdf_path = project_root / "app" / "uploads" / filename

    loader = PyPDFLoader(str(pdf_path))
    documents = loader.load()

    
    return documents

def split_documents(documents: list[Document]) -> list[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
    )
    chunks = text_splitter.split_documents(documents)

    print(f"Split into {len(chunks)} chunks")
    return chunks

def get_embeddings() -> OpenAIEmbeddings:
    embeddings = OpenAIEmbeddings(
        model=settings.openai_embeddings_model,
        api_key=settings.openai_api_key,
    )
    return embeddings

def enrich_metadata(chunks: list[Document],filename: str)-> list[Document]:
    document_id = str(uuid.uuid4())
    
    enriched_chunks = []

    for chunk_index, chunk in enumerate(chunks):

        metadata = {
            **chunk.metadata,
            "document_id": document_id,
            "chunk_id": chunk_index,
            "filename": filename
        }

        enriched_chunks.append(
            Document(
                page_content=chunk.page_content,
                metadata=metadata,
            )
        )

    return enriched_chunks

def get_qdrant_client() -> QdrantClient:
    client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
    )
    return client

def create_qdrant_collection(client: QdrantClient):
    if not client.collection_exists(settings.qdrant_collection_name):
        client.create_collection(
            collection_name=settings.qdrant_collection_name,
            vectors_config=VectorParams(
                size=1536,
                distance=Distance.COSINE,
            ),
        )
        print(f"Created collection {settings.qdrant_collection_name}")
    else:
        print(f"Collection {settings.qdrant_collection_name} already exists")
        
def create_payload_index(client: QdrantClient):
    collection = client.get_collection(settings.qdrant_collection_name)
    payload_schema = collection.payload_schema

    field_name = "metadata.filename"

    if field_name in payload_schema:
        print(f"Payload index '{field_name}' already exists.")
        return

    client.create_payload_index(
        collection_name=settings.qdrant_collection_name,
        field_name="metadata.filename",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    print(f"Created payload index: {field_name}")
        
def delete_qdrant_collection(client:QdrantClient,filename: str):
    return client.delete_collection(filename)
 
def get_vector_store(client:QdrantClient,embeddings:OpenAIEmbeddings)->QdrantVectorStore:
       
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=settings.qdrant_collection_name,
        embedding=embeddings,
    )
    
    return vector_store

def main():
    filename = "attention.pdf"
    documents = load_pdf(filename)
    print(f"Loaded {len(documents)} pages from {filename}")
    chunks = split_documents(documents)
    # print("Before:", chunks[0].metadata)
    chunks = enrich_metadata(chunks,filename)
    # print("After: ",chunks[0].metadata)
    embeddings = get_embeddings()
    
    client = get_qdrant_client()
    # delete_qdrant_collection(client,"documents")
    create_qdrant_collection(client)
    create_payload_index(client)
    
    vector_store = get_vector_store(client,embeddings)
    vector_store.add_documents(chunks)

    print(f"Indexed {len(chunks)} chunks into Qdrant collection {settings.qdrant_collection_name}")
    print("Indexing complete.")

if __name__ == "__main__":
    main()
    
#  uv run python demo/index_pipeline.y
# python -m demo.index_pipeline