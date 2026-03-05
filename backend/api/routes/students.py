"""Endpoints para estudiantes y tesistas."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from database.session import get_db

router = APIRouter(prefix="/students", tags=["students"])


@router.get("")
def list_students(
    q: Optional[str] = Query(None, description="Buscar por nombre, email o universidad"),
    status: Optional[str] = Query(None, description="Filtrar por estado: Activo, Graduado, etc."),
    program: Optional[str] = Query(None, description="Filtrar por programa"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Lista estudiantes/tesistas con filtros opcionales."""
    base = "FROM students WHERE 1=1"
    params: dict = {}

    if q:
        base += " AND (full_name ILIKE :q OR email ILIKE :q OR university ILIKE :q)"
        params["q"] = f"%{q}%"
    if status:
        base += " AND status = :status"
        params["status"] = status
    if program:
        base += " AND program ILIKE :program"
        params["program"] = f"%{program}%"

    total = db.execute(text(f"SELECT COUNT(*) {base}"), params).scalar()

    params["offset"] = (page - 1) * limit
    params["limit"] = limit

    rows = db.execute(text(f"""
        SELECT id, full_name, email, rut, university, program, status,
               start_date, graduation_date, tutor_name, co_tutor_name,
               wp_id, created_at, updated_at
        {base}
        ORDER BY full_name
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
