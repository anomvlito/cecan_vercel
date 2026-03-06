# Referencia de API

**Base URL producción:** `https://<dominio>.vercel.app/api`
**Base URL local:** `http://localhost:8000`
**Documentación interactiva:** `http://localhost:8000/docs` (Swagger UI)

---

## Resumen de endpoints

```mermaid
mindmap
  root(("/api"))
    publications
      POST /upload
      POST /{id}/enrich-doi
      GET /
      GET /{id}
      DELETE /{id}
    journals
      GET /
    researchers
      GET /
    students
      GET /
    projects
      GET /
    project-activities
      GET /
      POST /
      PUT /{id}
      DELETE /{id}
    responsibilities
      GET /
      POST /
      DELETE /{id}
      GET /my-tasks
      GET /my-tasks/members
    gantt
      GET /project/{id}
      PUT /task/{id}
      POST /links
      DELETE /links/{id}
    research-map
      GET /
    graph
      GET /data
    health
      GET /
```

---

## Publicaciones

### `POST /api/publications/upload`

Sube un PDF, extrae DOI automáticamente y enriquece con métricas JCR.

**Content-Type:** `multipart/form-data`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `file` | File | PDF (max 50MB) |
| `manual_doi` | string? | DOI manual (opcional, sobreescribe extracción) |

**Respuesta `201`:**
```json
{
  "publication": {
    "id": 42,
    "title": "Deep Learning for...",
    "doi": "10.1000/xyz123",
    "year": 2024,
    "status": "enriched",
    "quartile_snapshot": "Q1",
    "impact_factor_snapshot": 8.23,
    "jif_percentile_snapshot": 92.5,
    "journal": { "title": "Nature Machine Intelligence", "issn": "2522-5839" }
  },
  "doi_found": true,
  "doi": "10.1000/xyz123",
  "doi_method": "pdf_text",
  "journal_found": true,
  "message": "Revista encontrada: Nature Machine Intelligence (Q1, IF 8.23)"
}
```

**Errores:**

| Código | Condición |
|--------|-----------|
| `400` | No es un PDF o supera 50MB |
| `409` | DOI ya existe en la BD |
| `422` | Error de validación |

---

### `POST /api/publications/{id}/enrich-doi`

Enriquece una publicación existente con un DOI ingresado manualmente.

**Body JSON:**
```json
{ "doi": "10.1000/xyz123" }
```

**Respuesta `200`:** mismo formato que `upload`

---

### `GET /api/publications`

Lista todas las publicaciones, ordenadas por fecha de creación descendente.

**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "title": "...",
    "doi": "10.xxx/yyy",
    "year": 2023,
    "status": "complete",
    "quartile_snapshot": "Q2",
    "impact_factor_snapshot": 4.1,
    "is_top10": false,
    "journal": { ... }
  }
]
```

---

### `DELETE /api/publications/{id}`

Elimina una publicación.

**Respuesta:** `204 No Content`
**Error:** `404` si no existe

---

## Revistas JCR

### `GET /api/journals`

Búsqueda full-text con filtros en el catálogo JCR (35k+ registros).

**Query params:**

| Param | Tipo | Descripción |
|-------|------|-------------|
| `q` | string | Búsqueda en título, ISSN, publisher, categoría, país |
| `quartile` | string | Filtrar por cuartil: `Q1`, `Q2`, `Q3`, `Q4` |
| `min_percentile` | float | Percentil mínimo (0–100) |
| `max_percentile` | float | Percentil máximo (0–100) |
| `page` | int | Página (default: 1) |
| `limit` | int | Resultados por página (default: 50) |

**Respuesta `200`:**
```json
{
  "items": [ { "id": 1, "title": "...", "issn": "...", "impact_factor": 8.2, "quartile_rank": "Q1" } ],
  "total": 8420,
  "page": 1,
  "limit": 50,
  "pages": 169
}
```

---

## Investigadores

### `GET /api/researchers`

| Param | Tipo | Descripción |
|-------|------|-------------|
| `q` | string | Búsqueda en nombre, email, institución |
| `member_type` | string | `researcher` / `staff` |
| `is_active` | bool | Solo miembros activos |
| `page` | int | |
| `limit` | int | |

---

## Estudiantes

### `GET /api/students`

| Param | Tipo | Descripción |
|-------|------|-------------|
| `q` | string | Nombre, email, RUT |
| `status` | string | Estado del estudiante |
| `program` | string | Programa de postgrado |
| `page` | int | |
| `limit` | int | |

---

## Proyectos

### `GET /api/projects`

| Param | Tipo | Descripción |
|-------|------|-------------|
| `q` | string | Título, código, descripción |
| `status` | string | Activo / Finalizado / En pausa / Pendiente |
| `grant_type` | string | Tipo de financiamiento |
| `page` | int | |
| `limit` | int | |

---

## Actividades de proyecto

### `GET /api/project-activities?project_id={id}`

Lista actividades de un proyecto.

### `POST /api/project-activities`

```json
{
  "project_id": 5,
  "description": "Análisis de datos",
  "start_month": 3,
  "end_month": 6,
  "status": "pending"
}
```

### `PUT /api/project-activities/{id}`

Actualiza estado, progreso, presupuesto, pago.

```json
{
  "status": "in_progress",
  "progress": 45,
  "budget_allocated": 5000000,
  "payment_status": "parcial"
}
```

### `DELETE /api/project-activities/{id}`

**Respuesta:** `204 No Content`

---

## RACI y Mis Tareas

### `GET /api/responsibilities?resource_type=activity&resource_id={id}`

Lista asignaciones RACI de una actividad.

### `POST /api/responsibilities`

```json
{
  "resource_type": "activity",
  "resource_id": 12,
  "raci_role": "R",
  "member_id": 7
}
```

**Roles RACI:**

| Rol | Significado |
|-----|-------------|
| `R` | Responsible — quien ejecuta |
| `A` | Accountable — quien responde |
| `C` | Consulted — quien da input |
| `I` | Informed — quien recibe info |

### `DELETE /api/responsibilities/{id}`

### `GET /api/my-tasks?member_id={id}`

Retorna todas las actividades con asignación RACI del miembro, incluyendo `is_overdue`.

### `GET /api/my-tasks/members`

Lista miembros que tienen asignaciones RACI en actividades.

---

## Gantt (DHTMLX)

### `GET /api/gantt/project/{id}`

Retorna datos en formato DHTMLX Gantt.

```json
{
  "data": [
    {
      "id": 1,
      "text": "Análisis inicial",
      "start_date": "2026-01-01",
      "end_date": "2026-03-31",
      "progress": 0.4,
      "status": "in_progress",
      "number": 1,
      "parent": 0,
      "color": "#3b82f6"
    }
  ],
  "links": [
    { "id": 1, "source": 1, "target": 2, "type": "0" }
  ]
}
```

**Tipos de link:** `"0"` FS · `"1"` SS · `"2"` FF · `"3"` SF

### `PUT /api/gantt/task/{id}`

Actualiza fechas al hacer drag en el Gantt. Convierte fechas absolutas de vuelta a `start_month`/`end_month` relativos al proyecto.

```json
{ "start_date": "2026-02-01", "end_date": "2026-04-30" }
```

### `POST /api/gantt/links`

```json
{ "source": 1, "target": 2, "type": "0" }
```

### `DELETE /api/gantt/links/{id}`

---

## Mapa 3D

### `GET /api/research-map`

```json
{
  "points": [
    {
      "id": 1, "x": 1.2, "y": -0.8, "z": 0.5,
      "cluster_id": 0, "cluster_label": "Machine Learning",
      "color": "#3b82f6",
      "publication_id": 42, "title": "Deep Learning for...",
      "year": 2024, "quartile": "Q1", "doi": "10.xxx/yyy"
    }
  ],
  "clusters": [
    { "id": 0, "label": "Machine Learning", "color": "#3b82f6", "count": 45 }
  ]
}
```

**Colores de cluster:**

| ID | Color | Hex |
|----|-------|-----|
| 0 | Azul | `#3b82f6` |
| 1 | Morado | `#8b5cf6` |
| 2 | Verde | `#22c55e` |
| 3 | Naranja | `#f97316` |
| 4 | Rosa | `#ec4899` |

---

## Grafo de colaboración

### `GET /api/graph/data`

```json
{
  "nodes": [
    { "id": "r_1", "label": "Dr. García", "group": "researcher", "size": 20 }
  ],
  "edges": [
    { "from": "r_1", "to": "wp_2", "label": "WP2" }
  ],
  "stats": { "total_researchers": 15, "total_projects": 8 }
}
```

---

## Health Check

### `GET /health`

```json
{ "status": "ok", "version": "1.0.0" }
```

---

## Códigos de respuesta

| Código | Significado |
|--------|-------------|
| `200` | OK |
| `201` | Creado |
| `204` | Sin contenido (DELETE exitoso) |
| `400` | Error de validación / datos incorrectos |
| `404` | Recurso no encontrado |
| `409` | Conflicto (ej: DOI duplicado) |
| `422` | Entidad no procesable (Pydantic) |
| `500` | Error interno del servidor |
