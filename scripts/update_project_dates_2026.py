"""Desplaza las fechas de todos los proyectos para que sean visibles en 2026."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from config import settings
import psycopg2


def main():
    db_url = settings.DATABASE_URL
    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    cur = conn.cursor()

    # Ver proyectos actuales
    cur.execute("SELECT id, title, start_date, end_date FROM scientific_projects ORDER BY id")
    rows = cur.fetchall()
    print(f"Proyectos encontrados: {len(rows)}")
    for r in rows:
        print(f"  [{r[0]}] {r[1][:40] if r[1] else '?':40s}  {r[2]} → {r[3]}")

    if not rows:
        print("No hay proyectos.")
        conn.close()
        return

    # Calcular cuántos años desplazar para que end_date >= 2026-01-01
    # Tomar el proyecto más reciente
    cur.execute("SELECT MAX(end_date) FROM scientific_projects WHERE end_date IS NOT NULL")
    max_end = cur.fetchone()[0]

    if max_end and max_end.year >= 2026:
        print("\nLos proyectos ya tienen fechas en 2026 o posterior. No se requiere actualización.")
        conn.close()
        return

    # Calcular años a sumar
    target_year = 2026
    years_shift = target_year - (max_end.year if max_end else 2023)
    print(f"\nDesplazando fechas +{years_shift} año(s)...")

    cur.execute("""
        UPDATE scientific_projects
        SET
            start_date = start_date + (INTERVAL '1 year' * %(y)s),
            end_date   = end_date   + (INTERVAL '1 year' * %(y)s)
        WHERE start_date IS NOT NULL OR end_date IS NOT NULL
    """, {"y": years_shift})

    updated = cur.rowcount
    conn.commit()
    print(f"Actualizados: {updated} proyectos\n")

    # Mostrar resultado
    cur.execute("SELECT id, title, start_date, end_date FROM scientific_projects ORDER BY id")
    for r in cur.fetchall():
        print(f"  [{r[0]}] {str(r[1])[:40]:40s}  {r[2]} → {r[3]}")

    # También actualizar actividades (start_date / end_date calculados)
    cur2 = conn.cursor()
    cur2.execute("""
        UPDATE project_activities
        SET
            start_date = start_date + (INTERVAL '1 year' * %(y)s),
            end_date   = end_date   + (INTERVAL '1 year' * %(y)s)
        WHERE start_date IS NOT NULL OR end_date IS NOT NULL
    """, {"y": years_shift})
    conn.commit()
    print(f"\nActividades actualizadas: {cur2.rowcount}")

    cur.close()
    cur2.close()
    conn.close()
    print("\nListo.")


if __name__ == "__main__":
    main()
