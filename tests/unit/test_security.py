from app.core.security import has_valid_pdf_signature


def test_accepts_pdf_signature_within_header():
    assert has_valid_pdf_signature(b"%PDF-1.7\ncontent")
    assert has_valid_pdf_signature(b"\xef\xbb\xbf\n%PDF-1.4\ncontent")


def test_rejects_spoofed_or_late_pdf_signature():
    assert not has_valid_pdf_signature(b"MZ executable content")
    assert not has_valid_pdf_signature(b"x" * 1024 + b"%PDF-1.7")
