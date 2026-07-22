from pathlib import Path
from app.ai.pdf_loader import load_pdf

documents = load_pdf(Path("/Users/pink/python_project/enterprise-ai-workspace/app/uploads/attention.pdf"))

print(len(documents))
print(documents[0])

# uv run python -m app.playground.pdf_loader