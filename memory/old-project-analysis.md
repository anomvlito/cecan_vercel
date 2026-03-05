# Análisis Proyecto Antiguo — cecan-proyect

Fuente: `/home/fabian/src/cecan-proyect/cecan-frontend/`
Stack: React 18 + TypeScript + TanStack Table + Zustand + Tailwind

## Componentes de Publicaciones (15 componentes)

| Componente | Tamaño | Descripción |
|------------|--------|-------------|
| Publications.tsx (página) | ~3000 líneas | Página principal con tabla, filtros y modales |
| PublicationsFilters.tsx | - | Panel de filtros (8 tipos) |
| PublicationExpandedRow.tsx | 24 KB | Fila expandible con métricas detalladas |
| PublicationCard.tsx | - | Tarjeta para vista grid |
| UploadZone.tsx | - | Drag & drop múltiples PDFs |
| UploadStatusPanel.tsx | - | Panel flotante historial de cargas |
| DoiCell.tsx | - | Celda DOI editable con validación |
| UrlCell.tsx | 4.1 KB | Celda URL editable |
| AuthorsList.tsx | - | Lista autores compacto/expandido |
| StatusBadge.tsx | - | Badge de estado con emoji |
| SmartMaintenanceMenu.tsx | - | Dropdown acciones mantenimiento |
| ManualDoiEntry.tsx | - | Input manual de DOI |
| OpenAlexSearchModal.tsx | - | Modal búsqueda en OpenAlex |
| AttachPdfZone.tsx | - | Adjuntar PDF a publicación existente |
| AuthorInferenceModal.tsx | 11 KB | Modal autores inferidos con IA |
| ExperimentalDoiLab.tsx | 14 KB | Laboratorio experimental DOI |
| WosVerificationCard.tsx | - | Tarjeta verificación WOS |

## Hook Principal: usePublications.ts

Filtros disponibles:
- searchTerm (título, año, autores, journal)
- complianceFilter: all | compliant | non-compliant (has_funding_ack)
- journalFilter: dropdown dinámico
- yearFilter: dropdown dinámico
- quartileFilter: Q1-Q4
- top10Filter: boolean (percentile >= 90)
- noQuartileFilter: boolean (invertido)
- noDoiFilter: boolean (invertido)

## Columnas de la Tabla

1. Checkbox (selección múltiple)
2. Expand/Collapse icon
3. Título (clickeable)
4. Año
5. Autores (AuthorsList)
6. Revista/Journal
7. DOI (DoiCell con validación + copia)
8. Estado (StatusBadge)
9. Cuartil (Q1-Q4 badge coloreado)
10. Acciones (Edit, Delete)

Row expandible: PublicationExpandedRow

## StatusBadge Mapping

- metadata_only → 📄 Sin PDF (amber)
- pdf_attached → 📎 PDF Adjuntado (blue)
- content_enriched → 📝 Con Resumen (blue)
- journal_linked → 🔗 Revista Vinculada (yellow)
- fully_enriched → ✅ Completo (green)
- generating_summaries → ⏳ Procesando... (purple, pulse)

## PublicationExpandedRow — Secciones

1. WOS Verification Card (condicional)
2. Título completo
3. AttachPdfZone (si sin PDF y sin enriquecimiento)
4. Resumen bilingüe ES/EN con toggle (o botón "Generar con IA")
5. Métricas de revista: IF, IF-5yr, CiteScore, Quartile, Percentile, Categorías
6. OpenAlex Metadata: journal, año, citas, tema, OA badge
7. Legacy metrics (fallback)
8. Texto extraído (preview 500 chars)
9. Audit details (fecha + notas)

## Tipo Publication (antiguo, más complejo)

Campos adicionales respecto al nuevo:
- authors: Author[]
- has_funding_ack: boolean (compliance)
- local_path, enrichment_status
- content, summary_es, summary_en
- journal_name_temp, publisher_temp
- impact_metrics: { citation_count, ranking_percentile, quartile, jif, is_international_collab }
- metrics_data (OpenAlex raw)
- ai_journal_analysis (estimación IA con categorías)
- wos_verification
- last_audit_date, audit_notes
- canonical_doi, doi_verification_status
- url

## Store: uiStore.ts (Zustand)

viewMode: 'table' | 'grid' — persistido en localStorage

## Paleta de Colores (igual al nuevo)

- Primario: blue-600, indigo-600
- Q1: green, Q2: blue, Q3: yellow, Q4: red
- Success: emerald-500
- Warning: amber-500
- Error: red-500

## Endpoints API del Proyecto Antiguo (implícitos)

- GET /publications
- GET /publications/{id}
- POST /publications/upload
- POST /publications/{id}/attach-pdf
- PUT /publications/{id}
- PUT /publications/{id}/doi
- POST /publications/{id}/link-openalex
- POST /publications/{id}/enrich-journal
- POST /publications/{id}/generate-summaries
- POST /publications/audit
- POST /publications/search-openalex
