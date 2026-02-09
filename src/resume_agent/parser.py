"""Resume text extraction from PDF and DOCX files."""

from pathlib import Path

import pdfplumber
from docx import Document


def parse_resume(file_path: str) -> str:
    """Extract text from a resume file (PDF or DOCX).

    Returns the full text content of the resume.
    Raises ValueError on unsupported format or empty extraction.
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        text = _parse_pdf(path)
    elif ext == ".docx":
        text = _parse_docx(path)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use PDF or DOCX.")

    if not text.strip():
        raise ValueError(f"No text could be extracted from {path.name}.")

    return text.strip()


def _parse_pdf(path: Path) -> str:
    """Extract text from a PDF using pdfplumber."""
    try:
        pages = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages.append(page_text)
        return "\n\n".join(pages)
    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {e}") from e


def _parse_docx(path: Path) -> str:
    """Extract text from a DOCX using python-docx."""
    try:
        doc = Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        raise ValueError(f"Failed to parse DOCX: {e}") from e
