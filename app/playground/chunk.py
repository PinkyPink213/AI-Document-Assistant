from pathlib import Path

from app.ai.pdf_loader import load_pdf
from app.ai.text_splitter import get_text_splitter

documents = load_pdf(
    Path("/Users/pink/python_project/enterprise-ai-workspace/app/uploads/attention.pdf")
)

splitter = get_text_splitter()

chunks = splitter.split_documents(documents)

for chunk in chunks:

    chunk.metadata["conversation_id"] = conversation.id

    chunk.metadata["document_id"] = document.id

    chunk.metadata["filename"] = document.filename

print("Length of chunks:", len(chunks))

print("First chunk:", chunks[0])

# uv run python -m app.playground.chunk