"""Endpoints para actividades de proyectos (Gantt)."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from database.session import get_db

router = APIRouter(prefix="/project-activities", tags=["project-activities"])


class ActivityCreate(BaseModel):
    project_id: int
    description: str
    number: Optional[int] = None
    start_month: int = 1
    end_month: int = 1
    status: str = "pending"
    progress: int = 0
    budget_allocated: Optional[float] = None
    notes: Optional[str] = None
    sort_order: int = 0


class ActivityUpdate(BaseModel):
    description: Optional[str] = None
    number: Optional[int] = None
    start_month: Optional[int] = None
    end_month: Optional[int] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    budget_allocated: Optional[float] = None
    payment_status: Optional[str] = None
    payment_proof_url: Optional[str] = None
    sort_order: Optional[int] = None
    notes: Optional[str] = None


@router.get("")
def list_activities(
    project_id: int = Query(..., description="ID del proyecto"),
    db: Session = Depends(get_db),
) -> list:
    """Lista actividades de un proyecto con responsables RACI."""
    rows = db.execute(text("""
        SELECT
            pa.id,
            pa.project_id,
            pa.number,
            pa.description,
            pa.start_month,
            pa.end_month,
            pa.status,
            pa.progress,
            pa.budget_allocated,
            pa.payment_status,
            pa.payment_proof_url,
            pa.sort_order,
            pa.notes,
            pa.created_at,
            sp.start_date AS project_start_date,
            sp.title AS project_title
        FROM project_activities pa
        JOIN scientific_projects sp ON sp.id = pa.project_id
        WHERE pa.project_id = :project_id
        ORDER BY pa.sort_order, pa.number, pa.id
    """), {"project_id": project_id}).fetchall()

    items = []
    for r in rows:
        item = dict(r._mapping)
        # Calcular fechas reales a partir de start_month / end_month
        project_start = item.get("project_start_date")
        sm = item.get("start_month")
        em = item.get("end_month")
        if project_start and sm is not None and em is not None:
            from dateutil.relativedelta import relativedelta
            start = project_start + relativedelta(months=int(sm) - 1)
            end = project_start + relativedelta(months=int(em)) - relativedelta(days=1)
            item["start_date"] = start.isoformat()
            item["end_date"] = end.isoformat()
        else:
            item["start_date"] = None
            item["end_date"] = None
        items.append(item)

    return items


@router.post("", status_code=201)
def create_activity(
    body: ActivityCreate,
    db: Session = Depends(get_db),
) -> dict:
    """Crea una nueva actividad en el proyecto."""
    # Verificar que el proyecto existe
    proj = db.execute(
        text("SELECT id FROM scientific_projects WHERE id = :id"),
        {"id": body.project_id},
    ).fetchone()
    if not proj:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    row = db.execute(text("""
        INSERT INTO project_activities
            (project_id, number, description, start_month, end_month,
             status, progress, budget_allocated, notes, sort_order)
        VALUES
            (:project_id, :number, :description, :start_month, :end_month,
             :status, :progress, :budget_allocated, :notes, :sort_order)
        RETURNING *
    """), {
        "project_id": body.project_id,
        "number": body.number,
        "description": body.description,
        "start_month": body.start_month,
        "end_month": body.end_month,
        "status": body.status,
        "progress": body.progress,
        "budget_allocated": body.budget_allocated,
        "notes": body.notes,
        "sort_order": body.sort_order,
    }).fetchone()
    db.commit()
    return dict(row._mapping)


@router.put("/{activity_id}")
def update_activity(
    activity_id: int,
    body: ActivityUpdate,
    db: Session = Depends(get_db),
) -> dict:
    """Actualiza campos de una actividad."""
    existing = db.execute(
        text("SELECT * FROM project_activities WHERE id = :id"),
        {"id": activity_id},
    ).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        return dict(existing._mapping)

    set_clauses = ", ".join(f"{k} = :{k}" for k in updates)
    updates["id"] = activity_id

    row = db.execute(
        text(f"UPDATE project_activities SET {set_clauses} WHERE id = :id RETURNING *"),
        updates,
    ).fetchone()
    db.commit()
    return dict(row._mapping)


@router.delete("/{activity_id}", status_code=204)
def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Elimina una actividad."""
    result = db.execute(
        text("DELETE FROM project_activities WHERE id = :id"),
        {"id": activity_id},
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
