"""Docling / PyMuPDF PDF text extraction with OCR fallback."""

from app.infrastructure.pdf.extractor import extract_text_from_pdf, is_scanned_pdf


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF with OCR fallback for scanned documents."""
    return extract_text_from_pdf(pdf_path)