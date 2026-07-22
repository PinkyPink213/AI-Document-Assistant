from io import BytesIO

from langchain_core.documents import Document
from pypdf import PdfReader


def load_pdf(pdf_bytes: bytes, filename: str) -> list[Document]:
    """
    Load a PDF from bytes and return its pages as LangChain Documents.
    """
    reader = PdfReader(BytesIO(pdf_bytes))

    documents = []

    for page_number, page in enumerate(reader.pages):
        text = page.extract_text() or ""

        documents.append(
            Document(
                page_content=text,
                metadata={
                    "filename": filename,
                    "page": page_number + 1,
                    "total_pages": len(reader.pages)
                },
            )
        )

    return documents