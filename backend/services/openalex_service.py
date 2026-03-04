"""Cliente para OpenAlex API — obtiene ISSN y metadatos desde DOI."""
import httpx
from typing import Optional
from dataclasses import dataclass


OPENALEX_BASE = "https://api.openalex.org"
HEADERS = {"User-Agent": "CECAN-Platform/1.0 (mailto:cecan@cecan.cl)"}


@dataclass
class WorkMetadata:
    doi: str
    title: Optional[str]
    year: Optional[int]
    issn: Optional[str]
    eissn: Optional[str]
    journal_name: Optional[str]
    publisher: Optional[str]
    volume: Optional[str]
    issue: Optional[str]
    pages: Optional[str]
    openalex_id: Optional[str]
    raw: dict


async def fetch_work_by_doi(doi: str) -> Optional[WorkMetadata]:
    """Consulta OpenAlex con un DOI y retorna metadatos del trabajo.

    Args:
        doi: DOI sin prefijo URL (e.g. '10.1016/j.example.2023.01.001')

    Returns:
        WorkMetadata o None si no se encuentra
    """
    url = f"{OPENALEX_BASE}/works/doi:{doi}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=HEADERS)

    if response.status_code != 200:
        return None

    data = response.json()
    venue = data.get("primary_location", {}) or {}
    source = venue.get("source") or {}

    issns = source.get("issn", []) or []
    issn_l = source.get("issn_l")

    issn = issns[0] if issns else issn_l
    eissn = issns[1] if len(issns) > 1 else None

    return WorkMetadata(
        doi=doi,
        title=data.get("title"),
        year=data.get("publication_year"),
        issn=_clean_issn(issn),
        eissn=_clean_issn(eissn),
        journal_name=source.get("display_name"),
        publisher=source.get("publisher"),
        volume=data.get("biblio", {}).get("volume"),
        issue=data.get("biblio", {}).get("issue"),
        pages=_extract_pages(data.get("biblio", {})),
        openalex_id=data.get("id"),
        raw=data,
    )


def _clean_issn(issn: Optional[str]) -> Optional[str]:
    if not issn:
        return None
    return issn.replace("-", "").strip() if "-" not in issn else issn.strip()


def _extract_pages(biblio: dict) -> Optional[str]:
    first = biblio.get("first_page")
    last = biblio.get("last_page")
    if first and last:
        return f"{first}-{last}"
    return first or last or None
