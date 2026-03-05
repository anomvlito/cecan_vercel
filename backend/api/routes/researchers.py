"""Endpoints para investigadores y miembros académicos."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from database.session import get_db

router = APIRouter(prefix="/researchers", tags=["researchers"])


@router.get("")
def list_researchers(
    q: Optional[str] = Query(None, description="Buscar por nombre, email o institución"),
    member_type: Optional[str] = Query(None, description="Filtrar por tipo: researcher, staff, etc."),
    is_active: Optional[bool] = Query(None, description="Solo activos"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Lista investigadores/miembros con filtros opcionales."""
    base = """
        FROM academic_members am
        LEFT JOIN researcher_details rd ON rd.member_id = am.id
        WHERE 1=1
    """
    params: dict = {}

    if q:
        base += " AND (am.full_name ILIKE :q OR am.email ILIKE :q OR am.institution ILIKE :q)"
        params["q"] = f"%{q}%"
    if member_type:
        base += " AND am.member_type = :member_type"
        params["member_type"] = member_type
    if is_active is not None:
        base += " AND am.is_active = :is_active"
        params["is_active"] = is_active

    total = db.execute(text(f"SELECT COUNT(*) {base}"), params).scalar()

    params["offset"] = (page - 1) * limit
    params["limit"] = limit

    rows = db.execute(text(f"""
        SELECT
            am.id, am.full_name, am.email, am.rut, am.institution,
            am.member_type, am.wp_id, am.is_active, am.created_at,
            rd.orcid, rd.first_name, rd.last_name, rd.category,
            rd.citaciones_totales, rd.indice_h, rd.works_count,
            rd.i10_index, rd.url_foto, rd.start_date, rd.end_date
        {base}
        ORDER BY am.full_name
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
