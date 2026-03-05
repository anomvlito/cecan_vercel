# Referencia de API

Base URL en producción: `https://<dominio>.vercel.app/api`
Base URL en local: `http://localhost:8000`

Swagger interactivo (local): http://localhost:8000/docs

---

## Publicaciones

### `POST /publications/upload`

Sube un PDF y/o DOI para crear una publicación con métricas JCR.

**Content-Type:** `multipart/form-data`

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `file` | File (PDF) | Condicional | Archivo PDF. Máx 50 MB. |
| `doi` | string | Condicional | DOI manual. Tiene precedencia sobre extracción automática. |

Se requiere al menos uno de los dos campos.

**Modos de uso:**

| file | doi | Comportamiento |
|------|-----|---------------|
| ✅ | - | Extrae DOI automáticamente del PDF |
| ✅ | ✅ | Usa el DOI provisto, omite extracción |
| - | ✅ | Crea publicación solo con metadatos del DOI |

**Respuesta exitosa** `201 Created`:

```json
{
  "publication": {
    "id": 42,
    "title": "Deep Learning for ...",
    "doi": "10.1016/j.neunet.2024.001",
    "year": 2024,
    "pdf_filename": "paper.pdf",
    "status": "enriched",
    "journal_id": 1234,
    "impact_factor_snapshot": 8.2,
    "quartile_snapshot": "Q1",
    "jif_percentile_snapshot": 94.5,
    "is_top10": true,
    "journal": {
      "id": 1234,
      "issn": "0893-6080",
      "title": "Neural Networks",
      "impact_factor": 8.2,
      "quartile_rank": "Q1",
      "jif_percentile": 94.5,
      ...
    }
  },
  "doi_found": true,
  "doi": "10.1016/j.neunet.2024.001",
  "doi_method": "pdf_text",
  "journal_found": true,
  "journal": { ... },
  "message": "Revista vinculada exitosamente. Q1, IF: 8.2"
}
```

**Errores:**

| Código | Causa |
|--------|-------|
| `400` | No se proporcionó file ni doi, o archivo no es PDF |
| `409` | Ya existe una publicación con ese DOI |
| `413` | Archivo supera 50 MB |

---

### `POST /publications/{id}/enrich-doi`

Enriquece una publicación existente con un DOI ingresado manualmente.

**Content-Type:** `multipart/form-data`

| Campo | Tipo | Requerido |
|-------|------|-----------|
| `doi` | string | ✅ |

**Respuesta exitosa** `200 OK`: mismo formato que `UploadResult` arriba.

**Errores:**

| Código | Causa |
|--------|-------|
| `404` | Publicación no encontrada |
| `409` | El DOI ya pertenece a otra publicación |

---

### `GET /publications`

Lista todas las publicaciones ordenadas por fecha de creación (más reciente primero).

**Respuesta** `200 OK`:

```json
[
  {
    "id": 42,
    "title": "...",
    "doi": "...",
    "year": 2024,
    "status": "enriched",
    "quartile_snapshot": "Q1",
    "impact_factor_snapshot": 8.2,
    "is_top10": false,
    "journal": { ... }
  },
  ...
]
```

---

### `GET /publications/{id}`

Obtiene una publicación por ID.

**Errores:**

| Código | Causa |
|--------|-------|
| `404` | Publicación no encontrada |

---

## Posibles estados de `Publication.status`

| Valor | Descripción |
|-------|-------------|
| `uploaded` | PDF recibido, no se encontró DOI |
| `doi_extracted` | DOI encontrado, revista no vinculada |
| `enriched` | DOI + revista JCR + métricas completas |

---

## Métodos de extracción de DOI (`doi_extraction_method`)

| Valor | Descripción |
|-------|-------------|
| `pdf_text` | Extraído del texto del PDF con regex |
| `metadata` | Extraído de los metadatos XMP/PDF |
| `manual` | Ingresado manualmente por el usuario |
| `not_found` | No se encontró DOI |
