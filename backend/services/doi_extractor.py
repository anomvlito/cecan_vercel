"""Extrae DOIs desde texto de PDFs usando múltiples estrategias."""
import re
from typing import Optional

DOI_PATTERNS = [
    # Formato estándar con prefijo
    r"\b(10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+)",
    # Con prefijo doi: o DOI:
    r"(?:doi|DOI)\s*:?\s*(10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+)",
    # URL completa
    r"https?://(?:dx\.)?doi\.org/(10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+)",
]

# Caracteres no válidos al final del DOI
TRAILING_STRIP = r"[.,;)\]>\"'\s]+$"


def extract_doi_from_text(text: str) -> Optional[str]:
    """Extrae el primer DOI encontrado en el texto.

    Returns:
        DOI limpio sin prefijo (e.g. '10.1234/example') o None
    """
    for pattern in DOI_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            doi = match.group(1)
            doi = re.sub(TRAILING_STRIP, "", doi)
            return doi.strip()
    return None


def extract_doi_from_pdf_bytes(pdf_bytes: bytes) -> tuple[Optional[str], str]:
    """Extrae DOI desde bytes de un PDF.

    Returns:
        Tuple (doi, method) donde method es 'pdf_metadata' | 'pdf_text' | None
    """
    try:
        import pdfplumber
        import io

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            # 1. Intentar desde metadata
            meta = pdf.metadata or {}
            for key in ("doi", "DOI", "Subject", "Keywords"):
                value = meta.get(key, "")
                if value:
                    doi = extract_doi_from_text(str(value))
                    if doi:
                        return doi, "pdf_metadata"

            # 2. Buscar en primeras 3 páginas (donde suele estar el DOI)
            pages_to_check = min(3, len(pdf.pages))
            for i in range(pages_to_check):
                page_text = pdf.pages[i].extract_text() or ""
                doi = extract_doi_from_text(page_text)
                if doi:
                    return doi, "pdf_text"

    except Exception:
        pass

    return None, "not_found"
