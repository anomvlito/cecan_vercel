"""Busca revistas en la BD local (datos JCR) y deriva métricas de cuartil."""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from core.models import Journal

# ---------------------------------------------------------------------------
# Helpers de cálculo de cuartil y top 10%
# ---------------------------------------------------------------------------

_VALID_QUARTILES = {"Q1", "Q2", "Q3", "Q4"}


def derive_quartile(journal: Journal) -> Optional[str]:
    """Devuelve Q1/Q2/Q3/Q4 a partir de los campos del journal.

    Prioridad:
    1. category_ranking si ya es "Q1"…"Q4" (el Excel JCR a veces lo guarda aquí)
    2. quartile_rank si ya es "Q1"…"Q4"
    3. Parsear ranking "X/Y" de quartile_rank (posición/total)
    4. Parsear ranking "X/Y" de category_ranking
    5. Derivar desde jif_percentile
    """
    # 1 y 2: campo ya contiene el cuartil directo
    for raw in (journal.category_ranking, journal.quartile_rank):
        if raw:
            q = raw.strip().upper()
            if q in _VALID_QUARTILES:
                return q

    # 3 y 4: parsear formato "X/Y"
    for raw in (journal.quartile_rank, journal.category_ranking):
        if raw and "/" in raw:
            q = _quartile_from_ranking_str(raw)
            if q:
                return q

    # 5: desde percentil JIF
    if journal.jif_percentile is not None:
        return _quartile_from_percentile(journal.jif_percentile)

    return None


def derive_percentile(journal: Journal) -> Optional[float]:
    """Devuelve el percentil JIF (0–100) desde los campos del journal.

    Prioridad:
    1. jif_percentile (ya almacenado)
    2. Calcular desde ranking "X/Y": percentile = (1 - X/Y) * 100
    """
    if journal.jif_percentile is not None:
        return journal.jif_percentile

    for raw in (journal.quartile_rank, journal.category_ranking):
        if raw and "/" in raw:
            p = _percentile_from_ranking_str(raw)
            if p is not None:
                return p

    return None


def _quartile_from_ranking_str(raw: str) -> Optional[str]:
    try:
        parts = raw.strip().split("/")
        rank, total = int(parts[0]), int(parts[1])
        if total <= 0:
            return None
        return _quartile_from_ratio(rank / total)
    except (ValueError, IndexError, ZeroDivisionError):
        return None


def _percentile_from_ranking_str(raw: str) -> Optional[float]:
    try:
        parts = raw.strip().split("/")
        rank, total = int(parts[0]), int(parts[1])
        if total <= 0:
            return None
        return round((1 - rank / total) * 100, 2)
    except (ValueError, IndexError, ZeroDivisionError):
        return None


def _quartile_from_ratio(ratio: float) -> str:
    """Convierte posición relativa (0–1, menor = mejor) a cuartil."""
    if ratio <= 0.25:
        return "Q1"
    if ratio <= 0.50:
        return "Q2"
    if ratio <= 0.75:
        return "Q3"
    return "Q4"


def _quartile_from_percentile(pct: float) -> str:
    """Convierte JIF percentile (mayor = mejor) a cuartil."""
    if pct >= 75:
        return "Q1"
    if pct >= 50:
        return "Q2"
    if pct >= 25:
        return "Q3"
    return "Q4"


def find_journal_by_issn(db: Session, issn: str) -> Optional[Journal]:
    """Busca journal por ISSN o EISSN (normalizado sin guiones).

    Args:
        issn: ISSN con o sin guión (e.g. '1234-5678' o '12345678')
    """
    issn_clean = issn.replace("-", "").strip()
    issn_formatted = f"{issn_clean[:4]}-{issn_clean[4:]}" if len(issn_clean) == 8 else issn_clean

    return (
        db.query(Journal)
        .filter(
            or_(
                Journal.issn == issn_formatted,
                Journal.issn == issn_clean,
                Journal.eissn == issn_formatted,
                Journal.eissn == issn_clean,
            )
        )
        .first()
    )


def find_journal_by_title_and_publisher(
    db: Session, title: str, publisher: str
) -> Optional[Journal]:
    """Búsqueda por título exacto + publisher parcial (case-insensitive).

    El publisher de OpenAlex ("Multidisciplinary Digital Publishing Institute")
    raramente coincide exacto con el de JCR ("MDPI"). Usamos ILIKE con las
    primeras palabras para cubrir variantes del mismo publisher.
    """
    title_lower = title.lower().strip()
    # Tomar las primeras 2 palabras del publisher para mayor tolerancia a variantes
    publisher_words = publisher.strip().split()
    publisher_fragment = " ".join(publisher_words[:2]).lower()

    title_match = or_(
        func.lower(Journal.title) == title_lower,
        func.lower(Journal.title_abbrev) == title_lower,
        func.lower(Journal.iso_abbrev) == title_lower,
    )
    publisher_match = func.lower(Journal.publisher_name).contains(publisher_fragment)

    return (
        db.query(Journal)
        .filter(title_match, publisher_match)
        .first()
    )


def find_journal_by_title(db: Session, title: str) -> Optional[Journal]:
    """Búsqueda por título exacto (case-insensitive) o abreviatura. Sin publisher."""
    title_lower = title.lower().strip()

    return (
        db.query(Journal)
        .filter(
            or_(
                func.lower(Journal.title) == title_lower,
                func.lower(Journal.title_abbrev) == title_lower,
                func.lower(Journal.iso_abbrev) == title_lower,
            )
        )
        .first()
    )
