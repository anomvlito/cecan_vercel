"""Endpoints para proyectos científicos."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from database.session import get_db

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
def list_projects(
    q: Optional[str] = Query(None, description="Buscar por título, código o descripción"),
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    grant_type: Optional[str] = Query(None, description="Filtrar por tipo de fondo"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Lista proyectos científicos con filtros opcionales."""
    base = "FROM scientific_projects WHERE 1=1"
    params: dict = {}

    if q:
        base += " AND (title ILIKE :q OR code ILIKE :q OR description ILIKE :q OR pi_name ILIKE :q)"
        params["q"] = f"%{q}%"
    if status:
        base += " AND status = :status"
        params["status"] = status
    if grant_type:
        base += " AND grant_type ILIKE :grant_type"
        params["grant_type"] = f"%{grant_type}%"

    total = db.execute(text(f"SELECT COUNT(*) {base}"), params).scalar()

    params["offset"] = (page - 1) * limit
    params["limit"] = limit

    rows = db.execute(text(f"""
        SELECT id, title, code, work_package, grant_type, pi_id, pi_name,
               start_date, end_date, status, progress, budget_allocated,
               budget_executed, currency, years_covered, color, notes,
               created_at, updated_at
        {base}
        ORDER BY title
        LIMIT :limit OFFSET :offset
    """), params).fetchall()

    items = [dict(r._mapping) for r in rows]

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": max(1, -(-total // limit)),
    }
