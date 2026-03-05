# CECAN Vercel — Memoria del Proyecto

## Estado Actual (2026-03-05)

- **Backend** funcional en producción (Vercel + Supabase)
- **Frontend** minimalista: solo vista de upload PDF → resultado con métricas JCR
- **Flujo central**: PDF → DOI → OpenAlex (ISSN) → tabla `journals` en Supabase → métricas

## Bugs corregidos (2026-03-05)

- `_clean_issn` en openalex_service tenía lógica invertida (commit a266896)
- `journal` siempre era `None` en la respuesta del upload
- Mensaje "QQ1" por double-prefix en quartile_rank
- DOI duplicado lanzaba HTTP 500 → ahora 409 Conflict
- ISSN ordering no garantizado → ahora usa `issn_l` como primario + `issn_list` para búsqueda exhaustiva

## Archivos Clave

| Archivo | Descripción |
|---------|-------------|
| `backend/api/routes/publications.py` | Endpoint upload + get by id |
| `backend/services/openalex_service.py` | Cliente OpenAlex, WorkMetadata |
| `backend/services/journal_service.py` | Búsqueda journal por ISSN/título |
| `backend/services/doi_extractor.py` | Extracción DOI desde PDF |
| `backend/core/models.py` | SQLAlchemy: Publication, Journal |
| `backend/core/schemas.py` | Pydantic schemas |
| `frontend/src/views/UploadView.vue` | Vista upload (única actual) |
| `frontend/src/components/DropZone.vue` | Drag & drop PDF |
| `frontend/src/components/UploadResult.vue` | Resultado con métricas |
| `frontend/src/composables/useUploadPdf.ts` | Lógica de upload |
| `frontend/src/services/api.ts` | Axios client |
| `frontend/src/types/publication.ts` | Tipos TS: Publication, Journal |

## Proyecto Antiguo de Referencia

`/home/fabian/src/cecan-proyect/cecan-frontend/` — React + TypeScript
Ver detalle completo en `memory/old-project-analysis.md`

### Columnas de tabla que tenía el proyecto antiguo
Checkbox, Expand, Título, Año, Autores, Revista, DOI, Estado, Cuartil, Acciones

### Filtros que tenía
Search text, Año (dropdown), Revista (dropdown), Cuartil (Q1-Q4), Compliance, Top 10%, Sin Cuartil, Sin DOI

## Trabajo Pendiente

- [ ] `GET /publications` endpoint en backend (listar todas)
- [ ] Layout con sidebar izquierdo en Vue
- [ ] Vista PublicationsView con tabla
- [ ] Filtros básicos (search, año, cuartil)
- [ ] Integrar upload dentro del layout con sidebar
