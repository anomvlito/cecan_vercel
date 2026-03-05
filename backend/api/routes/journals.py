"""Endpoint para búsqueda y listado de revistas JCR con filtros."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, or_

from database.session import get_db
from core.models import Journal
from core.schemas import JournalRead, JournalListResponse

router = APIRouter(prefix="/journals", tags=["journals"])


def _derived_quartile():
    """Expresión SQLAlchemy que deriva el cuartil desde los campos disponibles.

    Prioridad (replica derive_quartile() de journal_service):
    1. category_ranking directo (Q1/Q2/Q3/Q4)
    2. quartile_rank directo (Q1/Q2/Q3/Q4)
    3. jif_percentile: ≥75→Q1, ≥50→Q2, ≥25→Q3, else Q4
    """
    return case(
        (
            func.upper(func.trim(Journal.category_ranking)).in_(["Q1", "Q2", "Q3", "Q4"]),
            func.upper(func.trim(Journal.category_ranking)),
        ),
        (
            func.upper(func.trim(Journal.quartile_rank)).in_(["Q1", "Q2", "Q3", "Q4"]),
            func.upper(func.trim(Journal.quartile_rank)),
        ),
        (Journal.jif_percentile >= 75, "Q1"),
        (Journal.jif_percentile >= 50, "Q2"),
        (Journal.jif_percentile >= 25, "Q3"),
        (Journal.jif_percentile.isnot(None), "Q4"),
        else_=None,
    )


@router.get("", response_model=JournalListResponse)
def list_journals(
    q: Optional[str] = Query(None, description="Búsqueda libre: título, ISSN, publisher, categoría, país"),
    quartile: Optional[str] = Query(None, description="Cuartiles separados por coma: Q1,Q2"),
    min_percentile: Optional[float] = Query(None, ge=0, le=100),
    max_percentile: Optional[float] = Query(None, ge=0, le=100),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> JournalListResponse:
    """Lista revistas con búsqueda full-text y filtros de cuartil/percentil."""
    query = db.query(Journal)

    # Búsqueda libre sobre múltiples campos
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Journal.title.ilike(term),
                Journal.title_abbrev.ilike(term),
                Journal.iso_abbrev.ilike(term),
                Journal.issn.ilike(term),
                Journal.eissn.ilike(term),
                Journal.publisher_name.ilike(term),
                Journal.categories_description.ilike(term),
                Journal.country.ilike(term),
            )
        )

    # Filtro por cuartil derivado
    if quartile:
        selected = [x.strip().upper() for x in quartile.split(",") if x.strip()]
        if selected:
            query = query.filter(_derived_quartile().in_(selected))

    # Filtro por percentil JIF
    if min_percentile is not None:
        query = query.filter(Journal.jif_percentile >= min_percentile)
    if max_percentile is not None:
        query = query.filter(Journal.jif_percentile <= max_percentile)

    total = query.count()
    offset = (page - 1) * limit
    items = (
        query
        .order_by(Journal.impact_factor.desc().nulls_last())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return JournalListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=max(1, -(-total // limit)),  # ceil division
    )
