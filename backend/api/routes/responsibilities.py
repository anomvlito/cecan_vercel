"""Endpoints para asignaciones RACI y mis tareas."""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from database.session import get_db

router = APIRouter(tags=["responsibilities"])


class ResponsibilityCreate(BaseModel):
    resource_type: str
    resource_id: int
    raci_role: str
    member_id: Optional[int] = None
    created_by: Optional[int] = None


# ─── Asignaciones RACI ────────────────────────────────────────────────────────

@router.get("/responsibilities")
def list_responsibilities(
    resource_type: str = Query(...),
    resource_id: int = Query(...),
    db: Session = Depends(get_db),
) -> list:
    """Lista asignaciones RACI con datos del miembro."""
    rows = db.execute(text("""
        SELECT
            ra.id,
            ra.resource_type,
            ra.resource_id,
            ra.raci_role,
            ra.member_id,
            ra.created_at,
            ra.created_by,
            am.full_name AS member_name,
            am.email AS member_email
        FROM responsibility_assignments ra
        LEFT JOIN academic_members am ON am.id = ra.member_id
        WHERE ra.resource_type = :resource_type
          AND ra.resource_id = :resource_id
        ORDER BY ra.raci_role, am.full_name
    """), {"resource_type": resource_type, "resource_id": resource_id}).fetchall()

    return [dict(r._mapping) for r in rows]


@router.post("/responsibilities", status_code=201)
def create_responsibility(
    body: ResponsibilityCreate,
    db: Session = Depends(get_db),
) -> dict:
    """Crea una asignación RACI."""
    if body.raci_role not in ("R", "A", "C", "I"):
        raise HTTPException(status_code=422, detail="raci_role debe ser R, A, C o I")

    row = db.execute(text("""
        INSERT INTO responsibility_assignments
            (resource_type, resource_id, raci_role, member_id, created_by)
        VALUES
            (:resource_type, :resource_id, :raci_role, :member_id, :created_by)
        RETURNING *
    """), {
        "resource_type": body.resource_type,
        "resource_id": body.resource_id,
        "raci_role": body.raci_role,
        "member_id": body.member_id,
        "created_by": body.created_by,
    }).fetchone()
    db.commit()
    return dict(row._mapping)


@router.delete("/responsibilities/{responsibility_id}", status_code=204)
def delete_responsibility(
    responsibility_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Elimina una asignación RACI."""
    result = db.execute(
        text("DELETE FROM responsibility_assignments WHERE id = :id"),
        {"id": responsibility_id},
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")


# ─── Mis Tareas ───────────────────────────────────────────────────────────────

@router.get("/my-tasks")
def my_tasks(
    member_id: Optional[int] = Query(None, description="Filtrar por miembro"),
    db: Session = Depends(get_db),
) -> list:
    """Todas las actividades con asignaciones RACI, proyectos y estado de vencimiento."""
    params: dict = {}
    extra_filter = ""
    if member_id is not None:
        extra_filter = "AND ra.member_id = :member_id"
        params["member_id"] = member_id

    rows = db.execute(text(f"""
        SELECT
            pa.id AS activity_id,
            pa.description AS activity_description,
            pa.status,
            pa.progress,
            pa.start_month,
            pa.end_month,
            sp.id AS project_id,
            sp.title AS project_title,
            sp.start_date AS project_start_date,
            ra.raci_role,
            am.id AS member_id,
            am.full_name AS member_name
        FROM responsibility_assignments ra
        JOIN project_activities pa ON pa.id = ra.resource_id AND ra.resource_type = 'activity'
        JOIN scientific_projects sp ON sp.id = pa.project_id
        LEFT JOIN academic_members am ON am.id = ra.member_id
        WHERE 1=1 {extra_filter}
        ORDER BY sp.title, pa.sort_order, pa.number
    """), params).fetchall()

    today = date.today()
    results = []
    for r in rows:
        item = dict(r._mapping)
        project_start = item.get("project_start_date")

        start_date = None
        end_date = None
        is_overdue = False

        if project_start:
            from dateutil.relativedelta import relativedelta
            start_date = project_start + relativedelta(months=item["start_month"] - 1)
            end_date = project_start + relativedelta(months=item["end_month"]) - relativedelta(days=1)
            if item.get("status") not in ("done",):
                is_overdue = end_date < today

        results.append({
            "activity_id": item["activity_id"],
            "activity_description": item["activity_description"],
            "project_title": item["project_title"],
            "project_id": item["project_id"],
            "raci_role": item["raci_role"],
            "member_name": item["member_name"],
            "member_id": item["member_id"],
            "status": item["status"],
            "progress": item["progress"],
            "start_date": start_date.isoformat()[:10] if start_date else None,
            "end_date": end_date.isoformat()[:10] if end_date else None,
            "is_overdue": is_overdue,
        })

    return results


@router.get("/my-tasks/members")
def my_tasks_members(db: Session = Depends(get_db)) -> list:
    """Lista de miembros que tienen al menos una asignación RACI en actividades."""
    rows = db.execute(text("""
        SELECT DISTINCT am.id, am.full_name, am.email
        FROM responsibility_assignments ra
        JOIN academic_members am ON am.id = ra.member_id
        WHERE ra.resource_type = 'activity'
          AND ra.member_id IS NOT NULL
        ORDER BY am.full_name
    """)).fetchall()
    return [dict(r._mapping) for r in rows]
