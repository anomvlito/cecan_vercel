"""Seed de usuarios de prueba en academic_members.

Crea investigadores principales, un miembro staff y deja al admin de Supabase intacto.
Idempotente: no duplica si el email ya existe.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from config import settings
import psycopg2


MEMBERS = [
    # Investigadores principales (PI)
    {
        "full_name": "Dra. María González Reyes",
        "email": "m.gonzalez@cecan.cl",
        "rut": "12.345.678-9",
        "institution": "Universidad de Chile",
        "member_type": "researcher",
        "wp_id": 1,
        "is_active": True,
        "details": {
            "first_name": "María",
            "last_name": "González Reyes",
            "category": "Investigadora Principal",
            "orcid": "0000-0001-2345-6789",
        },
    },
    {
        "full_name": "Dr. Carlos Mendoza Fuentes",
        "email": "c.mendoza@cecan.cl",
        "rut": "13.456.789-0",
        "institution": "Pontificia Universidad Católica",
        "member_type": "researcher",
        "wp_id": 2,
        "is_active": True,
        "details": {
            "first_name": "Carlos",
            "last_name": "Mendoza Fuentes",
            "category": "Investigador Principal",
            "orcid": "0000-0002-3456-7890",
        },
    },
    {
        "full_name": "Dra. Valentina Rojas Castro",
        "email": "v.rojas@cecan.cl",
        "rut": "14.567.890-1",
        "institution": "Universidad de Concepción",
        "member_type": "researcher",
        "wp_id": 3,
        "is_active": True,
        "details": {
            "first_name": "Valentina",
            "last_name": "Rojas Castro",
            "category": "Investigadora Asociada",
            "orcid": "0000-0003-4567-8901",
        },
    },
    {
        "full_name": "Dr. Andrés Herrera Lagos",
        "email": "a.herrera@cecan.cl",
        "rut": "15.678.901-2",
        "institution": "Universidad de Santiago",
        "member_type": "researcher",
        "wp_id": 4,
        "is_active": True,
        "details": {
            "first_name": "Andrés",
            "last_name": "Herrera Lagos",
            "category": "Investigador Asociado",
            "orcid": "0000-0004-5678-9012",
        },
    },
    # Staff
    {
        "full_name": "Felipe Soto Vargas",
        "email": "f.soto@cecan.cl",
        "rut": "16.789.012-3",
        "institution": "CECAN",
        "member_type": "staff",
        "wp_id": None,
        "is_active": True,
        "details": None,
    },
]


def main():
    db_url = settings.DATABASE_URL
    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    cur = conn.cursor()

    created = 0
    skipped = 0

    cur.execute("SELECT COALESCE(MAX(id), 0) FROM academic_members")
    next_id = cur.fetchone()[0] + 1
    cur.execute("SELECT COALESCE(MAX(id), 0) FROM researcher_details")
    next_rd_id = cur.fetchone()[0] + 1

    for m in MEMBERS:
        # Check duplicado por email
        cur.execute("SELECT id FROM academic_members WHERE email = %s", (m["email"],))
        existing = cur.fetchone()
        if existing:
            print(f"  SKIP (ya existe): {m['email']}")
            skipped += 1
            continue

        member_id = next_id
        next_id += 1
        cur.execute("""
            INSERT INTO academic_members (id, full_name, email, rut, institution, member_type, wp_id, is_active)
            VALUES (%(id)s, %(full_name)s, %(email)s, %(rut)s, %(institution)s, %(member_type)s, %(wp_id)s, %(is_active)s)
        """, {**m, "id": member_id})

        if m["details"]:
            d = m["details"]
            cur.execute("""
                INSERT INTO researcher_details (id, member_id, first_name, last_name, category, orcid)
                VALUES (%(id)s, %(member_id)s, %(first_name)s, %(last_name)s, %(category)s, %(orcid)s)
            """, {**d, "id": next_rd_id, "member_id": member_id})
            next_rd_id += 1

        print(f"  CREADO [{member_id}]: {m['full_name']} ({m['member_type']})")
        created += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"\nResumen: {created} creados, {skipped} omitidos.")


if __name__ == "__main__":
    main()
