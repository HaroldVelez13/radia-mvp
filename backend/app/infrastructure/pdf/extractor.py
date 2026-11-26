"""PDF text extraction with OCR fallback for scanned documents."""

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)


def is_scanned_pdf(pdf_path: str, text_threshold: int = 50) -> bool:
    """
    Detect if a PDF is scanned (image-based) by checking text content.

    Args:
        pdf_path: Path to the PDF file
        text_threshold: Minimum characters per page to consider as text-based

    Returns:
        True if PDF appears to be scanned (little/no extractable text), False otherwise
    """
    try:
        doc = fitz.open(pdf_path)
        total_text = 0
        page_count = len(doc)

        for page_num in range(page_count):
            page = doc[page_num]
            text = page.get_text()
            total_text += len(text.strip())

        doc.close()

        # Average characters per page
        avg_chars_per_page = total_text / page_count if page_count > 0 else 0

        logger.info(f"PDF {pdf_path}: {page_count} pages, avg {avg_chars_per_page:.0f} chars/page")

        return avg_chars_per_page < text_threshold

    except Exception as e:
        logger.warning(f"Error checking if PDF is scanned: {e}")
        return False


def extract_text_from_pdf(pdf_path: str, lang: str = "spa") -> str:
    """
    Extract text from PDF with OCR fallback for scanned documents.

    Args:
        pdf_path: Path to the PDF file
        lang: Tesseract language code (default: spa for Spanish)

    Returns:
        Extracted text as string
    """
    # First try standard text extraction with PyMuPDF
    try:
        doc = fitz.open(pdf_path)
        text_parts = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                text_parts.append(text)

        doc.close()

        extracted_text = "\n".join(text_parts)

        # If we got substantial text, return it
        if len(extracted_text.strip()) > 50:
            logger.info(f"Successfully extracted {len(extracted_text)} chars from {pdf_path} (standard)")
            return extracted_text

    except Exception as e:
        logger.warning(f"Standard text extraction failed: {e}")

    # Fallback to OCR with pytesseract
    logger.info(f"Falling back to OCR for {pdf_path}")
    return _extract_with_ocr(pdf_path, lang)


def _extract_with_ocr(pdf_path: str, lang: str = "spa") -> str:
    """
    Extract text using OCR (pytesseract) by rendering PDF pages as images.

    Args:
        pdf_path: Path to the PDF file
        lang: Tesseract language code

    Returns:
        Extracted text as string
    """
    try:
        doc = fitz.open(pdf_path)
        text_parts = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Render page as image (higher DPI for better OCR)
            pix = page.get_pixmap(dpi=300)
            img_data = pix.tobytes("png")

            # Convert to PIL Image
            image = Image.open(io.BytesIO(img_data))

            # Run OCR
            text = pytesseract.image_to_string(image, lang=lang)

            if text.strip():
                text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

        doc.close()

        result = "\n\n".join(text_parts)
        logger.info(f"OCR extracted {len(result)} chars from {pdf_path}")
        return result

    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        return f"Error OCR: {e}"


def extract_text_from_pdf_with_info(pdf_path: str, lang: str = "spa") -> dict:
    """
    Extract text with metadata about the extraction method.

    Returns:
        Dict with keys: text, method (standard/ocr), pages, chars
    """
    is_scanned = is_scanned_pdf(pdf_path)

    if is_scanned:
        text = _extract_with_ocr(pdf_path, lang)
        method = "ocr"
    else:
        doc = fitz.open(pdf_path)
        text_parts = [page.get_text() for page in doc]
        doc.close()
        text = "\n".join(text_parts)
        method = "standard"

    return {
        "text": text,
        "method": method,
        "pages": len(text.split("--- Page ")) - 1 if method == "ocr" else "unknown",
        "chars": len(text)
    }