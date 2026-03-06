"""Seed de cuentas de acceso en app_users.

Crea un app_user por cada academic_member registrado + el admin@cecan.cl.
Contraseña por defecto: cecan123

Idempotente: no duplica si el email ya existe.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from config import settings
from core.auth import hash_password
import psycopg2


DEFAULT_PASSWORD = "cecan123"

USERS = [
    # Admin del sistema (no vinculado a ningún academic_member)
    {"email": "admin@cecan.cl", "role": "admin", "academic_member_email": None},
    # Investigadores y staff (vinculados por email a academic_members)
    {"email": "m.gonzalez@cecan.cl", "role": "member", "academic_member_email": "m.gonzalez@cecan.cl"},
    {"email": "c.mendoza@cecan.cl", "role": "member", "academic_member_email": "c.mendoza@cecan.cl"},
    {"email": "v.rojas@cecan.cl", "role": "member", "academic_member_email": "v.rojas@cecan.cl"},
    {"email": "a.herrera@cecan.cl", "role": "member", "academic_member_email": "a.herrera@cecan.cl"},
    {"email": "f.soto@cecan.cl", "role": "member", "academic_member_email": "f.soto@cecan.cl"},
]


def main():
    conn = psycopg2.connect(settings.DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    # Asegurar que la tabla existe
    cur.execute("""
        CREATE TABLE IF NOT EXISTS app_users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            role VARCHAR(50) DEFAULT 'member',
            is_active BOOLEAN DEFAULT TRUE,
            academic_member_id INTEGER REFERENCES academic_members(id),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    hashed = hash_password(DEFAULT_PASSWORD)
    created = 0
    skipped = 0

    for u in USERS:
        # Skip si ya existe
        cur.execute("SELECT id FROM app_users WHERE email = %s", (u["email"],))
        if cur.fetchone():
            print(f"  SKIP (ya existe): {u['email']}")
            skipped += 1
            continue

        # Buscar academic_member_id si aplica
        member_id = None
        if u["academic_member_email"]:
            cur.execute(
                "SELECT id FROM academic_members WHERE email = %s",
                (u["academic_member_email"],),
            )
            row = cur.fetchone()
            member_id = row[0] if row else None

        cur.execute(
            """
            INSERT INTO app_users (email, hashed_password, role, is_active, academic_member_id)
            VALUES (%s, %s, %s, TRUE, %s)
            """,
            (u["email"], hashed, u["role"], member_id),
        )
        print(f"  CREADO [{u['role']}]: {u['email']} (member_id={member_id})")
        created += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"\nResumen: {created} creados, {skipped} omitidos.")
    print(f"Contraseña por defecto: {DEFAULT_PASSWORD}")


if __name__ == "__main__":
    main()
