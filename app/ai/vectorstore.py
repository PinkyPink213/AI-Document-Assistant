from langchain_qdrant import QdrantVectorStore
from qdrant_client.models import PayloadSchemaType
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_openai import OpenAIEmbeddings
from app.core.config  import settings

def get_qdrant_client() -> QdrantClient:
    client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
    )
    return client

def create_qdrant_collection(client: QdrantClient):
    print("Creating collection...")
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
        
def create_payload_index(client: QdrantClient, field_name: str):
    collection = client.get_collection(settings.qdrant_collection_name)
    payload_schema = collection.payload_schema

    if field_name in payload_schema:
        print(f"Payload index '{field_name}' already exists.")
        return

    client.create_payload_index(
        collection_name=settings.qdrant_collection_name,
        field_name=field_name,
        field_schema=PayloadSchemaType.KEYWORD,
    )
    print(f"Created payload index: {field_name}")

# def delete_qdrant_collection(client:QdrantClient,filename: str):
#     return client.delete_collection(filename)
    
def initialize_vectorstore(client: QdrantClient):
    """
    Initialize Qdrant collection and payload indexes.
    Run once when the application starts.
    """
    create_qdrant_collection(client)
    create_payload_index(client,"metadata.conversation_id")
    create_payload_index(client,"metadata.filename")

def get_vectorstore(client:QdrantClient, embeddings:OpenAIEmbeddings)->QdrantVectorStore:
       
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=settings.qdrant_collection_name,
        embedding=embeddings,
    )
    
    return vector_store