import re


PDF_HEADER_PATTERN = re.compile(rb"%PDF-\d\.\d")
PDF_HEADER_SCAN_BYTES = 1024


def has_valid_pdf_signature(content: bytes) -> bool:
    """Validate the PDF header from file content instead of trusting MIME type."""
    return bool(PDF_HEADER_PATTERN.search(content[:PDF_HEADER_SCAN_BYTES]))
