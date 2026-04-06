"""
PDF text extraction utility.
Converts each page of a PDF into plain text for downstream processing.
"""

from pypdf import PdfReader


def load_pdf(pdf_path: str) -> list[str]:
    """
    Read a PDF file and return a list where each element
    is the extracted text of one page.
    """
    reader = PdfReader(pdf_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text and text.strip():
            pages.append(text.strip())
    return pages


def load_pdf_as_string(pdf_path: str) -> str:
    """
    Read every page of the PDF and concatenate them
    into a single string separated by double newlines.
    """
    pages = load_pdf(pdf_path)
    return "\n\n".join(pages)
