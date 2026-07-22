from app.ai.embeddings import get_embeddings
from sklearn.metrics.pairwise import cosine_similarity

embedding = get_embeddings()

vector = embedding.embed_query(
    "What is FastAPI?"
)

print(len(vector))

a = embedding.embed_query("cat")
b = embedding.embed_query("kitten")
c = embedding.embed_query("docker")

print(cosine_similarity([a], [b]))
print(cosine_similarity([a], [c]))

# uv run python -m app.playground.embedding 
