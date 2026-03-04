"""Busca revistas en la BD local (datos JCR)."""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from core.models import Journal


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


def find_journal_by_title(db: Session, title: str) -> Optional[Journal]:
    """Búsqueda por título exacto (case-insensitive) o abreviatura."""
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
