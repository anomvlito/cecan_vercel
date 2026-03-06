-- Fix: agregar secuencias auto-increment a project_activities y responsibility_assignments
-- Ejecutar en Supabase SQL Editor si las tablas fueron creadas sin SERIAL

-- ── project_activities ──────────────────────────────────────────────────────
CREATE SEQUENCE IF NOT EXISTS project_activities_id_seq;

ALTER TABLE project_activities
  ALTER COLUMN id SET DEFAULT nextval('project_activities_id_seq'::regclass);

-- Posicionar la secuencia en el máximo id existente (evita conflictos)
SELECT setval(
  'project_activities_id_seq',
  COALESCE((SELECT MAX(id) FROM project_activities), 0) + 1,
  false
);

-- ── responsibility_assignments ──────────────────────────────────────────────
CREATE SEQUENCE IF NOT EXISTS responsibility_assignments_id_seq;

ALTER TABLE responsibility_assignments
  ALTER COLUMN id SET DEFAULT nextval('responsibility_assignments_id_seq'::regclass);

SELECT setval(
  'responsibility_assignments_id_seq',
  COALESCE((SELECT MAX(id) FROM responsibility_assignments), 0) + 1,
  false
);
