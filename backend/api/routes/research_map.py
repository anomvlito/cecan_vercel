"""Endpoint para el mapa de constelaciones de publicaciones."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from database.session import get_db

router = APIRouter(prefix="/research-map", tags=["research-map"])

CLUSTER_COLORS = {
    0: "#60a5fa",  # blue
    1: "#a78bfa",  # purple
    2: "#34d399",  # green
    3: "#fb923c",  # orange
    4: "#f472b6",  # pink
}


@router.get("")
def get_research_map(db: Session = Depends(get_db)):
    """Devuelve los puntos del mapa 3D con metadata de publicación."""
    rows = db.execute(text("""
        SELECT id, x, y, z, cluster_id, cluster_label, publication_id
        FROM research_map_points
        ORDER BY cluster_id, id
    """)).fetchall()

    points = []
    clusters: dict = {}

    for r in rows:
        cluster_id = r.cluster_id or 0
        color = CLUSTER_COLORS.get(cluster_id, "#94a3b8")

        point = {
            "id": r.id,
            "x": float(r.x),
            "y": float(r.y),
            "z": float(r.z),
            "cluster_id": cluster_id,
            "cluster_label": r.cluster_label or f"Cluster {cluster_id + 1}",
            "color": color,
            "publication_id": r.publication_id,
            "title": None,
            "year": None,
            "authors": None,
            "quartile": None,
            "doi": None,
        }
        points.append(point)

        if cluster_id not in clusters:
            clusters[cluster_id] = {
                "id": cluster_id,
                "label": r.cluster_label or f"Cluster {cluster_id + 1}",
                "color": color,
                "count": 0,
            }
        clusters[cluster_id]["count"] += 1

    return {
        "points": points,
        "clusters": list(clusters.values()),
        "total": len(points),
    }
