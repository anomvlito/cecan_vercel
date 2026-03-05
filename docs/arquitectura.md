# Arquitectura del Sistema

## Visión General

CECAN Vercel es una plataforma para gestión de publicaciones científicas. Permite subir PDFs de papers, extraer automáticamente su DOI, y vincularlos con métricas JCR (Journal Citation Reports) para obtener cuartil, Impact Factor y percentil.

```
┌─────────────────────────────────────────────────────────┐
│                        Usuario                          │
└─────────────────┬───────────────────────────────────────┘
                  │ HTTPS
┌─────────────────▼───────────────────────────────────────┐
│              Vercel (Edge / CDN)                        │
│  ┌─────────────────────┐  ┌──────────────────────────┐  │
│  │   Vue 3 SPA (dist)  │  │  FastAPI Serverless Fns  │  │
│  │   Vite + Tailwind   │  │  /api/* → Python 3.11    │  │
│  └─────────────────────┘  └──────────┬───────────────┘  │
└─────────────────────────────────────┼─────────────────--┘
                                       │
              ┌────────────────────────┼──────────────────┐
              │                        │                  │
   ┌──────────▼──────────┐  ┌──────────▼──────────┐       │
   │  Supabase PostgreSQL │  │  OpenAlex API       │       │
   │  - publications      │  │  (DOI → metadata)  │       │
   │  - journals (JCR)    │  └─────────────────────┘       │
   └──────────────────────┘                                │
```

## Stack Técnico

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Frontend | Vue 3 + Vite + TypeScript | Vue 3.x |
| Estilos | Tailwind CSS | v4 |
| Estado | Pinia | - |
| Backend | FastAPI | - |
| Runtime | Python | 3.11+ |
| ORM | SQLAlchemy | 2.0 |
| Base de datos | PostgreSQL (Supabase) | - |
| Deploy | Vercel | Serverless |

## Estructura del Monorepo

```
cecan_vercel/
├── backend/
│   ├── api/routes/
│   │   └── publications.py     # Endpoints REST
│   ├── core/
│   │   ├── models.py           # SQLAlchemy models (Journal, Publication)
│   │   └── schemas.py          # Pydantic schemas de entrada/salida
│   ├── services/
│   │   ├── doi_extractor.py    # Extrae DOI del texto del PDF
│   │   ├── openalex_service.py # Consulta OpenAlex por DOI
│   │   └── journal_service.py  # Busca y vincula revista JCR
│   ├── database/
│   │   └── session.py          # Sesión SQLAlchemy
│   └── main.py                 # Entry point FastAPI
├── frontend/
│   └── src/
│       ├── views/              # Páginas (router-level)
│       ├── components/         # Componentes reutilizables
│       ├── composables/        # Lógica reutilizable (useXxx)
│       ├── stores/             # Pinia stores
│       ├── services/api.ts     # Capa de llamadas HTTP (axios)
│       └── types/              # Interfaces TypeScript
├── scripts/                    # Seed / migración de datos JCR
├── docs/                       # Esta documentación
└── vercel.json                 # Configuración de rutas Vercel
```

## Modelo de Datos Principal

Ver [base-de-datos.md](./base-de-datos.md) para el esquema completo.

Las dos tablas centrales son:
- **`journals`** — ~35.000 filas importadas desde Excel JCR. Solo lectura en producción.
- **`publications`** — creadas al subir un PDF. Referencia a `journals` vía `journal_id`.

## Flujo Principal

Ver [flujo-upload.md](./flujo-upload.md) para el detalle completo del proceso de subida.

Resumen:
1. Usuario arrastra PDF → DropZone emite los archivos
2. Frontend llama `POST /api/publications/upload`
3. Backend extrae DOI del PDF (texto + metadatos)
4. Backend consulta OpenAlex para obtener ISSN de la revista
5. Backend busca el ISSN en tabla `journals`
6. Se guarda `Publication` y se retorna resultado con métricas

## API

Ver [api.md](./api.md) para referencia completa de endpoints.

Con backend local corriendo:
- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health
