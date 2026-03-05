"""Recalcula quartile_snapshot y jif_percentile_snapshot en publicaciones existentes.

Uso:
    python scripts/fix_publication_metrics.py
    python scripts/fix_publication_metrics.py --dry-run   # Solo muestra cambios, no guarda

El script carga cada publicación que tenga journal vinculado y recalcula los
campos de métricas usando la lógica correcta (derive_quartile / derive_percentile).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.orm import joinedload
from database.session import SessionLocal
from core.models import Publication
from services.journal_service import derive_quartile, derive_percentile


def fix_metrics(dry_run: bool = False) -> None:
    db = SessionLocal()
    try:
        pubs = (
            db.query(Publication)
            .options(joinedload(Publication.journal))
            .filter(Publication.journal_id.isnot(None))
            .all()
        )

        print(f"Publicaciones con journal vinculado: {len(pubs)}")
        if dry_run:
            print("MODO DRY-RUN — no se guardarán cambios\n")

        updated = 0
        unchanged = 0

        for pub in pubs:
            journal = pub.journal
            if not journal:
                continue

            new_quartile = derive_quartile(journal)
            new_percentile = derive_percentile(journal)

            old_quartile = pub.quartile_snapshot
            old_percentile = pub.jif_percentile_snapshot

            changed = (
                old_quartile != new_quartile
                or round(old_percentile or 0, 2) != round(new_percentile or 0, 2)
            )

            if changed:
                print(
                    f"  [{pub.id}] {(pub.title or pub.pdf_filename or '?')[:60]}"
                )
                print(f"         cuartil:   {old_quartile!r:12} → {new_quartile!r}")
                print(
                    f"         percentil: {old_percentile!r:12} → {new_percentile!r}"
                )
                if not dry_run:
                    pub.quartile_snapshot = new_quartile
                    pub.jif_percentile_snapshot = new_percentile
                updated += 1
            else:
                unchanged += 1

        if not dry_run and updated:
            db.commit()
            print(f"\n✓ {updated} publicaciones actualizadas, {unchanged} sin cambios.")
        else:
            print(f"\nResumen: {updated} tendrían cambios, {unchanged} sin cambios.")

    except Exception as exc:
        db.rollback()
        print(f"Error: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recalcular métricas de publicaciones")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostrar cambios sin guardar en la BD",
    )
    args = parser.parse_args()
    fix_metrics(dry_run=args.dry_run)
