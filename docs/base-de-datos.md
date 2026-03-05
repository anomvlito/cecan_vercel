# Modelo de Base de Datos

Base de datos: PostgreSQL vía Supabase.

---

## Tabla `journals`

Datos JCR importados desde el Excel oficial de Clarivate. Solo lectura en producción (~35.000 filas).

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | integer PK | - |
| `issn` | varchar(10) | ISSN impreso (índice) |
| `eissn` | varchar(10) | ISSN electrónico (índice) |
| `title` | varchar(500) | Nombre completo de la revista |
| `title_abbrev` | varchar(200) | Abreviatura |
| `iso_abbrev` | varchar(200) | Abreviatura ISO |
| `year` | integer | Año del reporte JCR |
| `impact_factor` | float | JIF (Journal Impact Factor) |
| `impact_factor_5yr` | float | JIF a 5 años |
| `eigenfactor` | float | Eigenfactor Score |
| `article_influence` | float | Article Influence Score |
| `immediacy_index` | float | Índice de inmediatez |
| `norm_eigenfactor` | float | Eigenfactor normalizado |
| `quartile_rank` | varchar(20) | Q1, Q2, Q3, Q4 (calculado del JIF percentile) |
| `jif_percentile` | float | Percentil JIF (0–100) |
| `category_ranking` | varchar(100) | Posición en categoría, ej: `15/250` |
| `categories_code` | varchar(200) | Códigos de categoría JCR |
| `categories_description` | text | Nombres de categorías |
| `edition` | varchar(20) | SCIE, SSCI, ESCI, etc. |
| `publisher_name` | varchar(500) | Editorial |
| `country` | varchar(100) | País de la editorial |
| `address` | text | Dirección editorial |
| `total_cites` | integer | Total de citas recibidas |
| `cited_half_life` | float | Vida media de citas |
| `created_at` | datetime | - |

### Lógica de cuartil

El campo `quartile_rank` se deriva del `jif_percentile` al momento de la importación:

| JIF Percentile | Cuartil |
|----------------|---------|
| ≥ 75 | Q1 |
| ≥ 50 | Q2 |
| ≥ 25 | Q3 |
| < 25 | Q4 |

### Top 10%

Una revista se considera "Top 10%" cuando `jif_percentile ≥ 90`. Este flag se calcula dinámicamente en el schema Pydantic (`is_top10`) a partir del snapshot guardado en `publications.jif_percentile_snapshot`.

---

## Tabla `publications`

Publicaciones científicas registradas por los usuarios.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | integer PK | - |
| `title` | varchar(1000) | Título del paper (de OpenAlex) |
| `doi` | varchar(300) UNIQUE | DOI del paper |
| `abstract` | text | Resumen (no usado aún) |
| `year` | integer | Año de publicación |
| `volume` | varchar(50) | Volumen de la revista |
| `issue` | varchar(50) | Número/issue |
| `pages` | varchar(100) | Rango de páginas |
| `pdf_filename` | varchar(500) | Nombre del archivo subido |
| `pdf_storage_path` | varchar(1000) | Path en Supabase Storage (futuro) |
| `journal_id` | integer FK | Referencia a `journals.id` (nullable) |
| `journal_issn_raw` | varchar(10) | ISSN detectado antes de vincular (debug) |
| `impact_factor_snapshot` | float | IF en el momento de vinculación |
| `quartile_snapshot` | varchar(5) | Cuartil en el momento de vinculación |
| `jif_percentile_snapshot` | float | Percentil en el momento de vinculación |
| `status` | varchar(50) | Estado del procesamiento |
| `doi_extraction_method` | varchar(50) | Cómo se obtuvo el DOI |
| `openalex_data` | text | JSON raw de la respuesta OpenAlex |
| `created_at` | datetime | - |
| `updated_at` | datetime | - |

### Snapshots de métricas

Los campos `*_snapshot` guardan los valores JCR **en el momento de la vinculación**. Esto es importante porque:

- Las métricas JCR cambian cada año
- La publicación puede haber sido indexada en un año diferente al actual
- El snapshot preserva la métrica histórica correcta

---

## Búsqueda de revista (journal matching)

El backend intenta vincular la publicación con una revista JCR siguiendo este orden:

1. **Por ISSN** — busca cada ISSN de la lista retornada por OpenAlex en `journals.issn` o `journals.eissn`
2. **Por nombre** — si ningún ISSN coincidió, busca por `journals.title` (ILIKE, case-insensitive)

Si ninguna estrategia encuentra la revista → `journal_id = null`, `status = "doi_extracted"`.

---

## Migración / Seed

Los datos JCR se importan desde un archivo CSV generado del Excel oficial:

```bash
# Desde la raíz del proyecto
python scripts/import_jcr.py  # importa scripts/jcr_import.csv a la tabla journals
```

La tabla `publications` se crea con SQLAlchemy:

```bash
# En Supabase: ejecutar el SQL generado por SQLAlchemy
# O via Alembic (si está configurado):
cd backend && .venv/bin/alembic upgrade head
```
