"""Importa datos del Excel JCR a la tabla journals en Supabase/PostgreSQL.

Uso:
    python scripts/import_jcr.py --file scripts/jcr_update.xlsx
    python scripts/import_jcr.py --file scripts/jcr_update.xlsx --batch-size 1000

Antes de correr, vaciar la tabla en Supabase:
    TRUNCATE TABLE journals RESTART IDENTITY CASCADE;
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import openpyxl
from database.session import SessionLocal, engine
from core.models import Base, Journal


COLUMN_MAP = {
    "ISSN": "issn",
    "EISSN": "eissn",
    "TITLE": "title",
    "TITLE20": "title_abbrev",
    "ISO_ABBREV": "iso_abbrev",
    "YEAR": "year",
    "IMFACT_FACTOR": "impact_factor",      # typo en el Excel original
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

_NULL_STRINGS = {None, "", "N/A", "n/a", "NULL", "null", "NA", "na"}


def clean_issn(value) -> str | None:
    if value in _NULL_STRINGS:
        return None
    s = str(value).strip()
    if not s or s in _NULL_STRINGS:
        return None
    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}-{s[4:]}"
    return s


def parse_float(value) -> float | None:
    if value in _NULL_STRINGS:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def parse_int(value) -> int | None:
    if value in _NULL_STRINGS:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def parse_str(value) -> str | None:
    if value in _NULL_STRINGS:
        return None
    s = str(value).strip()
    return s if s and s not in _NULL_STRINGS else None


def import_excel(filepath: str, batch_size: int = 1000) -> None:
    print(f"Abriendo {filepath}...")
    wb = openpyxl.load_workbook(filepath, read_only=True)

    sheet_name = "Journals"
    ws = wb[sheet_name] if sheet_name in wb.sheetnames else wb.active
    print(f"Leyendo hoja: '{ws.title}' (~{ws.max_row} filas)")

    headers = [str(cell.value).strip() if cell.value else "" for cell in next(ws.rows)]
    print(f"Columnas encontradas: {len(headers)}")

    col_idx = {col: i for i, col in enumerate(headers) if col in COLUMN_MAP}
    print(f"Columnas mapeadas: {list(col_idx.keys())}\n")

    if not col_idx:
        print("ERROR: ninguna columna del Excel coincide con el mapa esperado.")
        print(f"Cabeceras del Excel: {headers[:10]}")
        return

    Base.metadata.create_all(engine)
    db = SessionLocal()

    batch = []
    total = 0
    skipped = 0
    row_num = 1

    try:
        for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            title = parse_str(row[col_idx["TITLE"]]) if "TITLE" in col_idx else None
            if not title:
                skipped += 1
                continue

            record: dict = {}
            for excel_col, db_col in COLUMN_MAP.items():
                if excel_col not in col_idx:
                    continue
                val = row[col_idx[excel_col]]

                if db_col in ("issn", "eissn"):
                    record[db_col] = clean_issn(val)
                elif db_col in (
                    "impact_factor", "impact_factor_5yr", "eigenfactor",
                    "article_influence", "immediacy_index", "norm_eigenfactor",
                    "jif_percentile", "cited_half_life",
                ):
                    record[db_col] = parse_float(val)
                elif db_col in ("year", "total_cites"):
                    record[db_col] = parse_int(val)
                else:
                    record[db_col] = parse_str(val)

            batch.append(record)

            if len(batch) >= batch_size:
                db.bulk_insert_mappings(Journal, batch)
                db.commit()
                total += len(batch)
                batch = []
                print(f"  Insertados: {total:,} registros...", end="\r")

        if batch:
            db.bulk_insert_mappings(Journal, batch)
            db.commit()
            total += len(batch)

    except Exception as e:
        print(f"\nError en fila {row_num}: {e}")
        db.rollback()
    finally:
        wb.close()
        db.close()

    print(f"\nImportación completa: {total:,} journals insertados, {skipped:,} filas sin título omitidas")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Importar Excel JCR a PostgreSQL")
    parser.add_argument("--file", required=True, help="Ruta al archivo .xlsx")
    parser.add_argument("--batch-size", type=int, default=1000)
    args = parser.parse_args()

    import_excel(args.file, args.batch_size)
