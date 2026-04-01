# Modelo de Datos — CECAN Platform

## Diagrama Entidad-Relación (ERD)
La base de datos utiliza un modelo relacional en PostgreSQL para gestionar la complejidad de la producción científica y la planificación de proyectos.

```mermaid
erDiagram
    RESEARCHER ||--o{ PUBLICATION : authors
    JOURNAL ||--o{ PUBLICATION : publishes
    PROJECT ||--o{ ACTIVITY : contains
    ACTIVITY ||--o{ RESPONSIBILITY : carries
    RESEARCHER ||--o{ RESPONSIBILITY : assigned_to

    RESEARCHER {
        uuid id PK
        string full_name
        string email
        string institution
        string category
    }

    PUBLICATION {
        uuid id PK
        string title
        string doi
        uuid journal_id FK
        date publication_date
        string type
    }

    JOURNAL {
        uuid id PK
        string name
        string issn
        float impact_factor
        string quartile
        boolean is_top_10
    }

    PROJECT {
        uuid id PK
        string name
        date start_date
        date end_date
        string status
    }

    ACTIVITY {
        uuid id PK
        uuid project_id FK
        string name
        date due_date
        string status
    }

    RESPONSIBILITY {
        uuid id PK
        uuid activity_id FK
        uuid researcher_id FK
        string type "R/A/C/I"
    }
```

---

## Tablas Principales

### 1. `researchers`
Almacena el capital humano del centro, segmentado por categorías (Principal, Asociado, Adjunto, Estudiante).

### 2. `publications`
Represidat de la producción científica. Relaciona títulos y DOIs con sus respectivas métricas editoriales.

### 3. `journals`
Maestro de revistas científicas con snapshots anuales de métricas JCR (Journal Citation Reports).

### 4. Gestión de Actividades y Responsabilidades
Tabla vincular que permite definir roles (`Responsible`, `Accountable`, `Consulted`, `Informed`) en actividades específicas del proyecto para una futura automatización de notificaciones.
