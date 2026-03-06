# Flujos Principales

---

## 1. Flujo: Upload PDF → Enriquecimiento JCR

El flujo más importante del sistema. Un PDF se convierte en una publicación con métricas JCR.

```mermaid
sequenceDiagram
    actor U as Usuario
    participant FE as Frontend
    participant BE as Backend
    participant OA as OpenAlex API
    participant DB as Supabase DB

    U->>FE: Arrastra PDF o click "Subir PDF"
    FE->>BE: POST /api/publications/upload (multipart)

    BE->>BE: Validar PDF (tipo, tamaño ≤ 50MB)

    alt DOI manual enviado
        BE->>BE: Usar DOI manual
    else Sin DOI manual
        BE->>BE: extract_doi_from_pdf_bytes()
        Note over BE: 1° Metadata del PDF<br>2° Búsqueda regex en texto<br>3° Primeras 3 páginas
    end

    alt DOI encontrado
        BE->>OA: fetch_work_by_doi(doi)
        OA-->>BE: título, año, ISSNs, publisher, journal_name
        BE->>DB: find_journal_by_issn()
        alt ISSN encontrado
            DB-->>BE: Journal con métricas
        else ISSN no encontrado
            BE->>DB: find_journal_by_title_and_publisher()
            alt Título+Publisher encontrado
                DB-->>BE: Journal con métricas
            else No encontrado
                BE->>DB: find_journal_by_title()
            end
        end
    end

    alt Revista encontrada
        BE->>BE: derive_quartile() + derive_percentile()
        BE->>DB: Guardar Publication (status=enriched, snapshots)
        BE-->>FE: UploadResult (journal_found=true, Q1, IF 8.2)
        FE->>U: ✅ Notificación verde con métricas
    else Solo DOI, sin revista
        BE->>DB: Guardar Publication (status=doi_extracted)
        BE-->>FE: UploadResult (doi_found=true, journal_found=false)
        FE->>U: 🟦 Notificación índigo con opción de ingresar otro DOI
    else Sin DOI
        BE->>DB: Guardar Publication (status=uploaded)
        BE-->>FE: UploadResult (doi_found=false)
        FE->>U: 🟡 Notificación amarilla con campo para DOI manual
    end
```

### Estados posibles del resultado

| Color UI | Condición | Qué ver |
|----------|-----------|---------|
| 🟢 Verde | `journal_found=true` | Cuartil, IF, Percentil |
| 🟦 Índigo | `doi_found=true`, `journal_found=false` | DOI encontrado pero revista no en JCR |
| 🟡 Amarillo | `doi_found=false` | Sin DOI en PDF |
| 🔴 Rojo | `state=error` | Error de red o del servidor |

### Extracción de DOI

```mermaid
flowchart LR
    PDF["PDF bytes"]
    PDF --> M["1. Metadata\n(doi, Subject,\nKeywords)"]
    PDF --> T["2. Texto primeras\n3 páginas\n(regex)"]

    M -->|"encontrado"| DOI["DOI\n10.xxxx/yyyy"]
    T -->|"encontrado"| DOI
    M -->|"no"| T
    T -->|"no"| NULL["None\n(no encontrado)"]
```

---

## 2. Flujo: Gantt — Proyectos y Actividades

```mermaid
sequenceDiagram
    actor U as Usuario
    participant GV as GanttView
    participant BE as Backend
    participant DB as DB

    U->>GV: Selecciona proyecto
    GV->>BE: GET /api/gantt/project/{id}
    BE->>DB: Query activities + dependencies
    DB-->>BE: activities(start_month, end_month), links
    BE->>BE: Convertir meses relativos → fechas absolutas
    BE-->>GV: {data: [...tasks], links: [...deps]}
    GV->>GV: DHTMLX Gantt.parse(data)
    GV->>U: Barras de Gantt visualizadas

    U->>GV: Drag actividad a nuevas fechas
    GV->>BE: PUT /api/gantt/task/{id} {start_date, end_date}
    BE->>BE: Convertir fechas → start_month/end_month relativo
    BE->>DB: UPDATE project_activities
    DB-->>BE: OK
    BE-->>GV: Activity actualizada
```

### Conversión de meses relativos a fechas

```
project.start_date = 2026-01-01
activity.start_month = 3   →   start_date = 2026-03-01
activity.end_month   = 6   →   end_date   = 2026-06-30
```

Esta estrategia permite mover las fechas del proyecto sin tener que actualizar cada actividad individualmente.

---

## 3. Flujo: Mapa 3D de Publicaciones

```mermaid
sequenceDiagram
    participant HV as HomeView
    participant BE as Backend
    participant DB as DB
    participant TH as Three.js

    HV->>BE: GET /api/research-map
    BE->>DB: Query research_map_points + publications
    DB-->>BE: points(x,y,z,cluster_id), metadata
    BE-->>HV: {points: [...], clusters: [...]}

    HV->>TH: Inicializar Scene + Camera + Renderer
    HV->>TH: Crear esfera por cada punto (color por cluster)
    HV->>TH: Crear halos (BackSide material)
    HV->>TH: Trazar líneas intraclusters (distancia < 2.5)
    HV->>TH: Agregar starfield (800 partículas)
    HV->>TH: Iniciar loop de animación

    loop Cada frame
        TH->>TH: controls.update() + starField.rotation
        TH->>TH: Pulsar puntos (sin(t × 1.2 + i × 0.7) × 0.12)
        TH->>TH: Sincronizar slider zoom con camera.distance
    end

    HV->>HV: Raycaster detecta hover
    HV->>HV: Mostrar tooltip con metadata
```

---

## 4. Flujo: RACI — Asignación de Responsabilidades

```mermaid
sequenceDiagram
    actor U as Usuario
    participant GV as GanttView
    participant RP as RACI Panel
    participant BE as Backend

    U->>GV: Hover sobre fila de actividad
    GV->>GV: Mostrar íconos de acción (opacity-0 → opacity-100)
    U->>GV: Click ícono 👥 (Users)
    GV->>BE: GET /api/responsibilities?resource_type=activity&resource_id={id}
    BE-->>GV: Asignaciones RACI existentes
    GV->>RP: Abrir panel con asignaciones

    U->>RP: Ingresar member_id + rol (R/A/C/I)
    U->>RP: Click "Agregar"
    RP->>BE: POST /api/responsibilities {resource_type, resource_id, raci_role, member_id}
    BE-->>RP: ResponsibilityAssignment creada
    RP->>RP: Agregar a lista local (inmutable)

    U->>RP: Click eliminar asignación
    RP->>BE: DELETE /api/responsibilities/{id}
    RP->>RP: Filtrar de lista local
```

---

## 5. Flujo: Modo Leyendas Guía

```mermaid
stateDiagram-v2
    [*] --> Inactivo

    Inactivo --> Activo : Click "Activar leyendas guía"\nen Sidebar footer
    Activo --> Inactivo : Click "Desactivar leyendas"

    state Activo {
        [*] --> Visible
        Visible : GuideLabel activo en todas las vistas
        note right of Visible
            - Etiquetas azules sobre controles
            - Teleport to body
            - z-index 500
            - Se recalcula en scroll/resize
        end note
    }

    state Inactivo {
        [*] --> Oculto
        Oculto : Todas las GuideLabel ocultas
    }
```

**El estado NO persiste entre sesiones** — se resetea al recargar la página (comportamiento intencional).

---

## 6. Flujo: Búsqueda de Revistas JCR

```mermaid
flowchart TD
    Q["Query del usuario"]
    Q --> FT["Full-text search\nen título, ISSN,\npublisher, categoría, país"]
    FT --> FILT["Aplicar filtros\nquartile, percentile"]
    FILT --> PAG["Paginar resultados\npage, limit"]
    PAG --> RESP["Respuesta JSON\nitems[], total, pages"]

    subgraph "Derivación cuartil por item"
        J["Journal"] --> CR["category_ranking\n= Q1/Q2/Q3/Q4?"]
        CR -->|sí| OUT["Cuartil directo"]
        CR -->|no| QR["quartile_rank\n= Q1/Q2/Q3/Q4?"]
        QR -->|sí| OUT
        QR -->|"formato X/Y"| CALC["(1-X/Y)×100\n→ percentil"]
        CALC --> DER["≥75→Q1 ≥50→Q2\n≥25→Q3 <25→Q4"]
        QR -->|ninguno| JIF["jif_percentile"]
        JIF --> DER
        DER --> OUT
    end
```
