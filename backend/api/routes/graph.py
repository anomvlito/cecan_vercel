"""Endpoint para el mapa de colaboración (grafo de red)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from database.session import get_db

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/data")
def get_graph_data(db: Session = Depends(get_db)):
    """
    Construye nodos y aristas para vis-network cruzando:
    academic_members, researcher_details, work_packages,
    nodes, projects, project_researchers, project_nodes, member_wps
    """
    nodes = []
    edges = []
    node_ids: set = set()

    def add_node(n_id, **kwargs):
        if n_id not in node_ids:
            nodes.append({"id": n_id, **kwargs})
            node_ids.add(n_id)

    def add_edge(source, target, **kwargs):
        if source in node_ids and target in node_ids:
            edges.append({"from": source, "to": target, **kwargs})

    # ── 1. Investigadores ────────────────────────────────────────────────────
    researchers = db.execute(text("""
        SELECT
            am.id, am.full_name, am.email, am.institution, am.wp_id, am.is_active,
            rd.orcid, rd.category, rd.citaciones_totales, rd.indice_h,
            rd.works_count, rd.url_foto
        FROM academic_members am
        LEFT JOIN researcher_details rd ON rd.member_id = am.id
        WHERE am.member_type = 'researcher' AND am.is_active = TRUE
        ORDER BY am.full_name
    """)).fetchall()

    for r in researchers:
        node_id = f"inv_{r.id}"
        # Tamaño proporcional al h-index (base 20, máx ~55)
        h = r.indice_h or 0
        size = 20 + min(h * 0.6, 35)

        add_node(
            node_id,
            label=r.full_name,
            group="investigator",
            size=size,
            color={"background": "#e2e8f0", "border": "#94a3b8",
                   "highlight": {"background": "#bfdbfe", "border": "#3b82f6"}},
            data={
                "type": "Investigador",
                "name": r.full_name,
                "email": r.email,
                "institution": r.institution,
                "orcid": r.orcid,
                "category": r.category,
                "citations": r.citaciones_totales,
                "h_index": r.indice_h,
                "works": r.works_count,
                "photo": r.url_foto,
            },
        )

    # ── 2. Work Packages ─────────────────────────────────────────────────────
    wps = db.execute(text("SELECT id, name FROM work_packages ORDER BY id")).fetchall()
    for wp in wps:
        node_id = f"wp_{wp.id}"
        add_node(
            node_id,
            label=f"WP {wp.id}",
            title=wp.name,
            group="wp",
            size=50,
            shape="ellipse",
            color={"background": "#818cf8", "border": "#6366f1",
                   "highlight": {"background": "#a5b4fc", "border": "#4f46e5"}},
            font={"size": 16, "color": "#ffffff", "bold": True},
            data={"type": "WP", "name": wp.name},
        )

    # ── 3. Nodos Temáticos ───────────────────────────────────────────────────
    thematic = db.execute(text("SELECT id, name FROM nodes ORDER BY id")).fetchall()
    for n in thematic:
        node_id = f"nodo_{n.id}"
        add_node(
            node_id,
            label=n.name,
            group="nodo",
            shape="box",
            color={"background": "#164e63", "border": "#0e7490",
                   "highlight": {"background": "#0e7490", "border": "#06b6d4"}},
            font={"color": "#67e8f9", "size": 11},
            data={"type": "Nodo", "name": n.name},
        )

    # ── 4. Proyectos ─────────────────────────────────────────────────────────
    projects = db.execute(text(
        "SELECT id, title, wp_id FROM projects ORDER BY id"
    )).fetchall()

    for p in projects:
        node_id = f"proj_{p.id}"
        label = p.title[:28] + "…" if len(p.title) > 28 else p.title
        add_node(
            node_id,
            label=label,
            title=p.title,
            group="project",
            shape="diamond",
            size=18,
            color={"background": "#065f46", "border": "#059669",
                   "highlight": {"background": "#059669", "border": "#10b981"}},
            font={"color": "#6ee7b7", "size": 10},
            data={"type": "Proyecto", "name": p.title},
        )
        # Arista proyecto → WP
        if p.wp_id:
            add_edge(
                node_id, f"wp_{p.wp_id}",
                color={"color": "#a5b4fc", "opacity": 0.5},
                width=2, dashes=True,
            )

    # ── 5. Aristas investigador → WP (member_wps) ────────────────────────────
    mwps = db.execute(text("SELECT member_id, wp_id FROM member_wps")).fetchall()
    for mw in mwps:
        add_edge(
            f"inv_{mw.member_id}", f"wp_{mw.wp_id}",
            color={"color": "#6366f1", "opacity": 0.35},
            width=1,
        )

    # ── 6. Aristas proyecto → investigador (project_researchers) ─────────────
    pr_rows = db.execute(text(
        "SELECT project_id, member_id, role FROM project_researchers"
    )).fetchall()
    for pr in pr_rows:
        is_pi = pr.role and "responsable" in pr.role.lower()
        add_edge(
            f"proj_{pr.project_id}", f"inv_{pr.member_id}",
            color={"color": "#fca5a5" if is_pi else "#d1d5db",
                   "opacity": 0.8 if is_pi else 0.3},
            width=2 if is_pi else 1,
        )

    # ── 7. Aristas proyecto → nodo temático (project_nodes) ──────────────────
    pn_rows = db.execute(text(
        "SELECT project_id, node_id FROM project_nodes"
    )).fetchall()
    for pn in pn_rows:
        add_edge(
            f"proj_{pn.project_id}", f"nodo_{pn.node_id}",
            color={"color": "#a5f3fc", "opacity": 0.4},
            width=1,
        )

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "researchers": sum(1 for n in nodes if n.get("group") == "investigator"),
            "wps": sum(1 for n in nodes if n.get("group") == "wp"),
            "projects": sum(1 for n in nodes if n.get("group") == "project"),
            "nodes_thematic": sum(1 for n in nodes if n.get("group") == "nodo"),
            "edges": len(edges),
        },
    }
