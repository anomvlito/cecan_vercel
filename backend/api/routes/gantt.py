"""Endpoints DHTMLX Gantt — sirve datos en formato {data, links} y gestiona dependencias."""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from dateutil.relativedelta import relativedelta

from database.session import get_db

router = APIRouter(prefix="/gantt", tags=["gantt"])


# ── Modelos Pydantic ───────────────────────────────────────────────────────────

class TaskDrag(BaseModel):
    """Recibe nuevas fechas absolutas tras drag en DHTMLX y las convierte a meses."""
    start_date: str   # "YYYY-MM-DD"
    end_date: str     # "YYYY-MM-DD"


class LinkCreate(BaseModel):
    project_id: int
    source: int       # activity_id origen
    target: int       # activity_id destino
    type: str = "0"   # 0=FS, 1=SS, 2=FF, 3=SF


# ── Helpers ───────────────────────────────────────────────────────────────────

def _date_from_iso(s: str) -> date:
    return date.fromisoformat(s.split("T")[0])


STATUS_COLOR = {
    "pending":     "#94a3b8",
    "in_progress": "#3b82f6",
    "done":        "#22c55e",
    "blocked":     "#ef4444",
}


# ── GET /gantt/project/{project_id} ───────────────────────────────────────────

@router.get("/project/{project_id}")
def get_gantt_data(project_id: int, db: Session = Depends(get_db)) -> dict:
    """Retorna {data, links} en formato DHTMLX Gantt para un proyecto."""

    # Proyecto
    proj = db.execute(
        text("SELECT id, start_date, end_date FROM scientific_projects WHERE id = :id"),
        {"id": project_id},
    ).fetchone()
    if not proj:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    proj_start: Optional[date] = proj.start_date

    # Actividades
    acts = db.execute(text("""
        SELECT id, number, description, start_month, end_month,
               status, progress, budget_allocated, parent_id, sort_order
        FROM project_activities
        WHERE project_id = :pid
        ORDER BY sort_order, number, id
    """), {"pid": project_id}).fetchall()

    data = []
    for a in acts:
        sm, em = a.start_month, a.end_month
        if proj_start and sm and em:
            t_start = proj_start + relativedelta(months=int(sm) - 1)
            t_end   = proj_start + relativedelta(months=int(em))
        else:
            t_start = date.today()
            t_end   = date.today() + relativedelta(months=1)

        # Duración en días (DHTMLX la calcula desde start+end si se usa end_date)
        color = STATUS_COLOR.get(a.status, "#94a3b8")
        data.append({
            "id":         a.id,
            "text":       a.description,
            "start_date": t_start.strftime("%Y-%m-%d 00:00"),
            "end_date":   t_end.strftime("%Y-%m-%d 00:00"),
            "progress":   round((a.progress or 0) / 100, 2),
            "status":     a.status,
            "number":     a.number,
            "parent":     a.parent_id or 0,
            "color":      color,
            "textColor":  "#ffffff",
            "open":       True,
        })

    # Links / dependencias
    links_rows = db.execute(text("""
        SELECT id, source_id AS source, target_id AS target, link_type AS type
        FROM project_activity_links
        WHERE project_id = :pid
    """), {"pid": project_id}).fetchall()

    links = [
        {"id": r.id, "source": r.source, "target": r.target, "type": r.type}
        for r in links_rows
    ]

    return {"data": data, "links": links}


# ── PUT /gantt/task/{activity_id} — drag actualiza start/end month ─────────────

@router.put("/task/{activity_id}")
def update_task_dates(
    activity_id: int,
    body: TaskDrag,
    db: Session = Depends(get_db),
) -> dict:
    """Convierte fechas absolutas de DHTMLX a start_month/end_month y guarda."""

    act = db.execute(
        text("SELECT pa.*, sp.start_date AS proj_start FROM project_activities pa "
             "JOIN scientific_projects sp ON sp.id = pa.project_id WHERE pa.id = :id"),
        {"id": activity_id},
    ).fetchone()
    if not act:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")

    proj_start: Optional[date] = act.proj_start
    if not proj_start:
        raise HTTPException(status_code=422, detail="El proyecto no tiene fecha de inicio")

    new_start = _date_from_iso(body.start_date)
    new_end   = _date_from_iso(body.end_date)

    # Convertir a meses (1-based) relativos a inicio de proyecto
    start_month = (new_start.year - proj_start.year) * 12 + (new_start.month - proj_start.month) + 1
    end_month   = (new_end.year   - proj_start.year) * 12 + (new_end.month   - proj_start.month)

    # end_month mínimo = start_month
    end_month = max(end_month, start_month)

    db.execute(
        text("UPDATE project_activities SET start_month=:sm, end_month=:em WHERE id=:id"),
        {"sm": start_month, "em": end_month, "id": activity_id},
    )
    db.commit()
    return {"id": activity_id, "start_month": start_month, "end_month": end_month}


# ── POST /gantt/links ─────────────────────────────────────────────────────────

@router.post("/links", status_code=201)
def create_link(body: LinkCreate, db: Session = Depends(get_db)) -> dict:
    """Crea una dependencia entre dos actividades."""
    row = db.execute(text("""
        INSERT INTO project_activity_links (project_id, source_id, target_id, link_type)
        VALUES (:pid, :src, :tgt, :typ)
        RETURNING id, source_id AS source, target_id AS target, link_type AS type
    """), {
        "pid": body.project_id,
        "src": body.source,
        "tgt": body.target,
        "typ": body.type,
    }).fetchone()
    db.commit()
    return dict(row._mapping)


# ── DELETE /gantt/links/{link_id} ─────────────────────────────────────────────

@router.delete("/links/{link_id}", status_code=204)
def delete_link(link_id: int, db: Session = Depends(get_db)) -> None:
    """Elimina una dependencia."""
    result = db.execute(
        text("DELETE FROM project_activity_links WHERE id = :id"),
        {"id": link_id},
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Dependencia no encontrada")
