from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.core.config import settings

project_root = Path(__file__).resolve().parents[1]
pdf_path = project_root / "app" / "uploads" / "attention.pdf"

loader = PyPDFLoader(str(pdf_path))
documents = loader.load()

print(f"Loaded {len(documents)} pages")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,
    chunk_overlap=100,
)
chunks = text_splitter.split_documents(documents)

print(f"Split into {len(chunks)} chunks")

embeddings = OpenAIEmbeddings(
    model=settings.embedding_model,
    api_key=settings.openai_api_key,
)

client = QdrantClient(
    url=settings.qdrant_url,
    api_key=settings.qdrant_api_key,
)


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
    
    
vector_store = QdrantVectorStore(
    client=client,
    collection_name=settings.qdrant_collection_name,
    embedding=embeddings,
)

vector_store.add_documents(chunks)

print(f"Indexed {len(chunks)} chunks into Qdrant collection {settings.qdrant_collection_name}")
print("Indexing complete.")


#  uv run python demo/index_pipeline.y
# python -m demo.index_pipeline