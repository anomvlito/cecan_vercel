-- Script para habilitar DHTMLX Gantt interactivo
-- Ejecutar en Supabase SQL Editor

-- 1. Agregar parent_id a project_activities (para sub-tareas)
ALTER TABLE project_activities
  ADD COLUMN IF NOT EXISTS parent_id INTEGER REFERENCES project_activities(id) ON DELETE SET NULL;

-- 2. Crear tabla de dependencias (flechas entre tareas)
CREATE TABLE IF NOT EXISTS project_activity_links (
  id          SERIAL PRIMARY KEY,
  project_id  INTEGER NOT NULL REFERENCES scientific_projects(id) ON DELETE CASCADE,
  source_id   INTEGER NOT NULL REFERENCES project_activities(id) ON DELETE CASCADE,
  target_id   INTEGER NOT NULL REFERENCES project_activities(id) ON DELETE CASCADE,
  link_type   VARCHAR(1) NOT NULL DEFAULT '0',  -- 0=FS, 1=SS, 2=FF, 3=SF
  created_at  TIMESTAMP DEFAULT NOW(),
  UNIQUE (source_id, target_id, link_type)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_links_project ON project_activity_links(project_id);
CREATE INDEX IF NOT EXISTS idx_links_source  ON project_activity_links(source_id);
CREATE INDEX IF NOT EXISTS idx_links_target  ON project_activity_links(target_id);
