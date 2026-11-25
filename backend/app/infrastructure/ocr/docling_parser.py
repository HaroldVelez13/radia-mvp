# Placeholder Docling / PyMuPDF
def extract_text_from_pdf(pdf_path: str) -> str:
    # T1.3
    try:
        import fitz
        doc = fitz.open(pdf_path)
        return "\n".join([page.get_text() for page in doc])
    except Exception as e:
        return f"Error OCR: {e}"
