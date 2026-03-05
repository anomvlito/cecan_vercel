"""Importa datos del Excel JCR a la tabla journals en Supabase/PostgreSQL.

Uso:
    python scripts/import_jcr.py --file data/jcr_update.xlsx
    python scripts/import_jcr.py --file data/jcr_update.xlsx --batch-size 500

El script es idempotente: usa upsert por (issn, year) para evitar duplicados.
"""
import argparse
import sys
from pathlib import Path

# Agregar backend/ al path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import openpyxl
from sqlalchemy.dialects.postgresql import insert as pg_insert
from database.session import SessionLocal, engine
from core.models import Base, Journal


COLUMN_MAP = {
    "ISSN": "issn",
    "EISSN": "eissn",
    "TITLE": "title",
    "TITLE20": "title_abbrev",
    "ISO_ABBREV": "iso_abbrev",
    "YEAR": "year",
    "IMFACT_FACTOR": "impact_factor",      # nota: typo en el Excel original
    "IMPACT_FACTOR_5YR": "impact_factor_5yr",
    "EIGENFACTOR": "eigenfactor",
    "ARTL_INFLUENCE": "article_influence",
    "IMMEDIACY_INDEX": "immediacy_index",
    "NORM_EIGENFACTOR": "norm_eigenfactor",
    "QUARTILE_RANK": "quartile_rank",
    "JIF_PERCENTILE": "jif_percentile",
    "CATEGORY_RANKING": "category_ranking",
    "CATEGORIES_CODE": "categories_code",
    "CATEGORIES_DESCRIPTION": "categories_description",
    "EDITION": "edition",
    "PUBLISHER_NAME": "publisher_name",
    "COUNTRY": "country",
    "ADDRESS": "address",
    "TOT_CITES": "total_cites",
    "CITED_HALF_LIFE": "cited_half_life",
}


def clean_issn(value) -> str | None:
    if not value:
        return None
    s = str(value).strip()
    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}-{s[4:]}"
    return s if s else None


def parse_float(value) -> float | None:
    try:
        return float(value) if value not in (None, "", "N/A", "n/a") else None
    except (ValueError, TypeError):
        return None


def parse_int(value) -> int | None:
    try:
        return int(value) if value not in (None, "", "N/A") else None
    except (ValueError, TypeError):
        return None


def import_excel(filepath: str, batch_size: int = 500) -> None:
    print(f"Abriendo {filepath}...")
    wb = openpyxl.load_workbook(filepath, read_only=True)
    ws = wb.active

    headers = [str(cell.value).strip() if cell.value else "" for cell in next(ws.rows)]
    print(f"Columnas encontradas: {len(headers)}")

    col_idx = {col: i for i, col in enumerate(headers) if col in COLUMN_MAP}
    print(f"Columnas mapeadas: {list(col_idx.keys())}")

    Base.metadata.create_all(engine)
    db = SessionLocal()

    batch = []
    total = 0
    errors = 0

    try:
        for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            title = row[col_idx.get("TITLE", -1)] if "TITLE" in col_idx else None
            if not title:
                continue

            record = {}
            for excel_col, db_col in COLUMN_MAP.items():
                if excel_col not in col_idx:
                    continue
                val = row[col_idx[excel_col]]

                if db_col in ("issn", "eissn"):
                    record[db_col] = clean_issn(val)
                elif db_col in ("impact_factor", "impact_factor_5yr", "eigenfactor",
                                "article_influence", "immediacy_index", "norm_eigenfactor",
                                "jif_percentile", "cited_half_life"):
                    record[db_col] = parse_float(val)
                elif db_col in ("year", "total_cites"):
                    record[db_col] = parse_int(val)
                elif val is not None:
                    record[db_col] = str(val).strip() or None
                else:
                    record[db_col] = None

            batch.append(record)

            if len(batch) >= batch_size:
                _upsert_batch(db, batch)
                total += len(batch)
                batch = []
                print(f"  Importados: {total} registros...", end="\r")

        if batch:
            _upsert_batch(db, batch)
            total += len(batch)

    except Exception as e:
        print(f"\nError en fila {row_num}: {e}")
        errors += 1
        db.rollback()
    finally:
        wb.close()
        db.close()

    print(f"\nImportación completa: {total} journals importados, {errors} errores")


def _upsert_batch(db, records: list[dict]) -> None:
    """Upsert batch usando PostgreSQL ON CONFLICT.

    Estrategia dual:
    - Con ISSN: ON CONFLICT (issn, year) — el índice único habitual
    - Sin ISSN: ON CONFLICT (title, year) — en PostgreSQL NULL != NULL,
      por lo que filas con issn=NULL nunca colisionan en el índice (issn, year)
      y se duplicarían en cada reimportación. Usamos (title, year) como
      clave alternativa para deduplicar.
    """
    with_issn = [r for r in records if r.get("issn")]
    without_issn = [r for r in records if not r.get("issn")]

    if with_issn:
        stmt = pg_insert(Journal).values(with_issn)
        stmt = stmt.on_conflict_do_update(
            index_elements=["issn", "year"],
            set_={col: stmt.excluded[col] for col in with_issn[0].keys() if col not in ("issn", "year")},
        )
        db.execute(stmt)

    if without_issn:
        stmt = pg_insert(Journal).values(without_issn)
        stmt = stmt.on_conflict_do_update(
            index_elements=["title", "year"],
            set_={col: stmt.excluded[col] for col in without_issn[0].keys() if col not in ("title", "year")},
        )
        db.execute(stmt)

    db.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Importar Excel JCR a PostgreSQL")
    parser.add_argument("--file", required=True, help="Ruta al archivo .xlsx")
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()

    import_excel(args.file, args.batch_size)
