"""Script temporal para crear las tablas del módulo Gantt + RACI en Supabase."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from config import settings
import psycopg2

DDL = """
CREATE TABLE IF NOT EXISTS project_activities (
    id SERIAL PRIMARY KEY,
    project_id INT NOT NULL REFERENCES scientific_projects(id) ON DELETE CASCADE,
    number INT,
    description TEXT NOT NULL,
    start_month INT NOT NULL DEFAULT 1,
    end_month INT NOT NULL DEFAULT 1,
    status VARCHAR(20) DEFAULT 'pending',
    progress INT DEFAULT 0,
    budget_allocated NUMERIC(14,2),
    payment_status VARCHAR(20) DEFAULT 'pending',
    payment_proof_url TEXT,
    sort_order INT DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS responsibility_assignments (
    id SERIAL PRIMARY KEY,
    resource_type VARCHAR(50) NOT NULL,
    resource_id INT NOT NULL,
    raci_role VARCHAR(1) NOT NULL,
    member_id INT REFERENCES academic_members(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by INT
);

CREATE INDEX IF NOT EXISTS idx_resource_lookup ON responsibility_assignments(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_member_lookup ON responsibility_assignments(member_id);
"""


def main() -> None:
    db_url = settings.DATABASE_URL
    # psycopg2 expects postgresql:// not postgresql+psycopg2://
    db_url = db_url.replace("postgresql+psycopg2://", "postgresql://")
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    print(f"Conectando a la base de datos...")
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()

    print("Ejecutando DDL...")
    cur.execute(DDL)

    print("Tablas creadas correctamente:")
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('project_activities', 'responsibility_assignments')
        ORDER BY table_name
    """)
    for row in cur.fetchall():
        print(f"  - {row[0]}")

    cur.close()
    conn.close()
    print("Listo.")


if __name__ == "__main__":
    main()
