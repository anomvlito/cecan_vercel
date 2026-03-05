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
    issn: Optional[str]       # ISSN primario (linking ISSN preferido)
    eissn: Optional[str]      # ISSN secundario
    issn_list: list[str]      # Todos los ISSNs disponibles para búsqueda exhaustiva
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

    issns_raw = source.get("issn", []) or []
    issn_l = source.get("issn_l")

    # issn_l es el "linking ISSN" — más estable para búsquedas
    # Usarlo como primario; el array puede contener print + electronic sin orden garantizado
    primary_raw = issn_l or (issns_raw[0] if issns_raw else None)
    secondary_raw = next(
        (i for i in issns_raw if _clean_issn(i) != _clean_issn(primary_raw)),
        None,
    )

    # Lista deduplicada de todos los ISSNs disponibles
    all_raw = ([issn_l] if issn_l else []) + issns_raw
    issn_list = list(dict.fromkeys(_clean_issn(i) for i in all_raw if i))

    return WorkMetadata(
        doi=doi,
        title=data.get("title"),
        year=data.get("publication_year"),
        issn=_clean_issn(primary_raw),
        eissn=_clean_issn(secondary_raw),
        issn_list=issn_list,
        journal_name=source.get("display_name"),
        publisher=source.get("publisher"),
        volume=data.get("biblio", {}).get("volume"),
        issue=data.get("biblio", {}).get("issue"),
        pages=_extract_pages(data.get("biblio", {})),
        openalex_id=data.get("id"),
        raw=data,
    )


def _clean_issn(issn: Optional[str]) -> Optional[str]:
    """Normaliza ISSN al formato estándar XXXX-XXXX."""
    if not issn:
        return None
    cleaned = issn.replace("-", "").strip().upper()
    if len(cleaned) == 8:
        return f"{cleaned[:4]}-{cleaned[4:]}"
    return cleaned


def _extract_pages(biblio: dict) -> Optional[str]:
    first = biblio.get("first_page")
    last = biblio.get("last_page")
    if first and last:
        return f"{first}-{last}"
    return first or last or None
