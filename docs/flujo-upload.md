# Flujo de Upload de Publicaciones

## Descripción General

El flujo de upload permite subir uno o varios PDFs simultáneamente. El sistema extrae automáticamente el DOI, consulta OpenAlex para obtener metadatos de la revista, y la vincula con las métricas JCR almacenadas localmente.

---

## Pipeline del Backend

```
PDF recibido
     │
     ▼
¿Tiene DOI manual?
  ├─ SÍ → usar DOI manual (doi_method = "manual")
  └─ NO  → extraer DOI del PDF (texto + metadatos XMP)
               └─ doi_method = "pdf_text" | "metadata" | null
     │
     ▼
¿Se encontró DOI?
  ├─ NO  → guardar Publication(status="uploaded"), retornar doi_found=false
  └─ SÍ → consultar OpenAlex
               │
               ▼
          ¿OpenAlex responde?
            ├─ NO  → guardar con DOI pero sin métricas
            └─ SÍ  → obtener lista de ISSNs y nombre de revista
                          │
                          ▼
                     Buscar ISSN en tabla `journals`
                     Si no: buscar por nombre de revista
                          │
                          ▼
                     ¿Revista encontrada en JCR?
                       ├─ SÍ → snapshot de métricas, status="enriched"
                       └─ NO  → status="doi_extracted", journal_id=null
```

### Campos del resultado (`UploadResult`)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `doi_found` | bool | Si se encontró DOI en el PDF o fue provisto manualmente |
| `doi` | string? | El DOI extraído/provisto |
| `doi_method` | string? | `"pdf_text"`, `"metadata"`, `"manual"` |
| `journal_found` | bool | Si se encontró la revista en la base JCR |
| `journal` | objeto? | Datos de la revista (IF, cuartil, etc.) |
| `publication` | objeto | La publicación creada en BD |
| `message` | string | Mensaje legible del resultado |

---

## Estados de una Publicación

```
uploaded → doi_extracted → enriched
                        ↘ (sin revista JCR)
```

| Status | Significado |
|--------|-------------|
| `uploaded` | PDF recibido, no se encontró DOI |
| `doi_extracted` | DOI encontrado pero revista no vinculada |
| `enriched` | DOI + revista JCR + métricas completas |

---

## Comportamiento del Frontend

### Soporte de múltiples archivos

Tanto en `/upload` como en `/publications`, el usuario puede:
- Arrastrar varios PDFs simultáneamente
- Seleccionar múltiples archivos desde el selector del sistema
- Cada archivo genera un **job** independiente con su propia notificación

### Notificaciones por job (4 casos)

Cada PDF subido genera una tarjeta de notificación con comportamiento distinto según el resultado:

---

#### ✅ Caso 1: Éxito — revista encontrada en JCR
**Color:** verde
**Auto-dismiss:** sí, a los **4 segundos**
**Muestra:** nombre del archivo · cuartil (Q1/Q2/Q3/Q4) · badge "Top 10%" si aplica · mensaje con IF

```
✓  paper_2024.pdf   [Q1]  [★ Top 10%]
   Revista vinculada exitosamente. Q1, IF: 8.2
```

---

#### 🔴 Caso 2: Error (duplicado u otro)
**Color:** rojo
**Auto-dismiss:** sí, a los **5 segundos**
**Muestra:** mensaje de error del backend (ej: "Ya existe una publicación con este DOI")

---

#### 🟡 Caso 3: DOI no encontrado en el PDF
**Color:** amarillo
**Auto-dismiss:** no (requiere acción del usuario)
**Muestra:** input para ingresar DOI manualmente

```
⚠  paper_sin_doi.pdf
   [Ingresa el DOI manualmente: 10.xxxx/...]  [Enriquecer]
```

El usuario puede tipear el DOI y presionar Enter o hacer click en "Enriquecer". Si la revista se encuentra tras el enriquecimiento, la tarjeta se auto-dismissea a los 4s.

---

#### 🟣 Caso 4: DOI encontrado pero revista NO está en la base JCR
**Color:** indigo/violeta
**Auto-dismiss:** no (requiere revisión del usuario)
**Muestra:** panel de auditoría con el DOI encontrado

```
🔍  paper_raro.pdf
   DOI encontrado: 10.1016/j.algo.2024.001
   Revista no encontrada en la base JCR local

   [10.1016/j.algo.2024.001]  [Copiar DOI]  [Abrir en CrossRef]

   Posibles causas: revista no indexada en JCR, ISSN no coincide,
   o fuera del período cubierto.
```

**Posibles causas de este caso:**
- La revista existe pero no está indexada en JCR (ej: revistas ESCI, predatorias, libros)
- El ISSN retornado por OpenAlex no coincide con ningún registro en la tabla `journals`
- La tabla JCR local cubre solo ciertos años y la revista no está en ese corte
- Error de OpenAlex: retornó un ISSN incorrecto

**Acciones disponibles:**
1. **Copiar DOI** — copia al portapapeles para investigar externamente
2. **Abrir en CrossRef** — abre `https://doi.org/{doi}` en nueva pestaña para ver los metadatos completos y el ISSN oficial
3. **Cerrar (X)** — descartar manualmente cuando el usuario haya tomado nota

---

## Enriquecimiento Manual (`POST /{id}/enrich-doi`)

Disponible cuando el PDF no tenía DOI (Caso 3). El usuario provee el DOI:

1. Backend recibe el DOI, consulta OpenAlex
2. Actualiza `title`, `year`, `volume`, `issue`, `pages` si no estaban
3. Busca la revista en JCR por ISSN o nombre
4. Actualiza los snapshots de métricas
5. Retorna un `UploadResult` con el resultado

Si el DOI ya pertenece a otra publicación, retorna `409 Conflict`.

---

## Detección de Duplicados

El campo `doi` en la tabla `publications` tiene constraint `UNIQUE`. Si se sube un PDF cuyo DOI ya existe, el backend retorna:

```
HTTP 409 Conflict
{"detail": "Ya existe una publicación con el DOI 10.xxxx/xxx (id=42)"}
```

En el frontend esto aparece como una notificación roja que se auto-dismissea en 5 segundos.
