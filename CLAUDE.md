# CLAUDE.md - CECAN Vercel Platform

Plataforma CECAN para gestión de publicaciones científicas. Monorepo con FastAPI backend y Vue 3 frontend, desplegado en Vercel con Supabase PostgreSQL.

## Stack

- **Backend**: FastAPI (Python 3.11+) — desplegado como Vercel Serverless Functions
- **Frontend**: Vue 3 + Vite + TypeScript + Tailwind CSS 4
- **Base de datos**: Supabase PostgreSQL
- **Storage**: Supabase Storage (PDFs)
- **Auth**: JWT via FastAPI

## Estructura del Proyecto

```
cecan_vercel/
├── backend/               # FastAPI app
│   ├── api/routes/        # Endpoints REST
│   ├── core/models.py     # SQLAlchemy models
│   ├── services/          # Lógica de negocio
│   ├── database/          # Sesión y repositorios
│   └── main.py            # Entry point
├── frontend/              # Vue 3 SPA
│   ├── src/
│   │   ├── views/         # Páginas (router-level)
│   │   ├── components/    # Componentes reutilizables
│   │   ├── composables/   # Vue composables (useXxx)
│   │   ├── stores/        # Pinia stores
│   │   ├── services/      # API calls (axios)
│   │   └── types/         # TypeScript types
│   └── vite.config.ts
├── scripts/               # Utilidades (seed, migration, etc.)
└── docs/                  # Documentación técnica
```

## Comandos de Desarrollo

```bash
# Backend (desde backend/)
python -m uvicorn main:app --reload --port 8000
.venv/bin/alembic upgrade head

# Frontend (desde frontend/)
npm run dev
npm run build
npm run typecheck

# Ambos (desde raíz)
make dev
```

## Variables de Entorno

Backend requiere `.env` en `backend/`:
```
DATABASE_URL=postgresql://...   # Supabase connection string
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx
GOOGLE_API_KEY=xxx              # Gemini AI
SECRET_KEY=xxx                  # JWT signing
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

## Arquitectura de Datos

### Flujo Principal: Upload PDF → Métricas Journal
1. Usuario sube PDF → Supabase Storage
2. Backend extrae texto → detecta DOI
3. Llama OpenAlex API con DOI → obtiene ISSN de la revista
4. Busca ISSN en tabla `journals` (importada desde JCR Excel)
5. Retorna métricas: Impact Factor, Quartile, JIF Percentile
6. Guarda `Publication` en BD con métricas vinculadas

### Tabla `journals` (35k+ registros desde JCR)
Campos clave: `issn`, `eissn`, `title`, `impact_factor`, `impact_factor_5yr`,
`quartile_rank`, `jif_percentile`, `eigenfactor`, `article_influence`,
`categories_description`, `publisher_name`, `country`, `year`

## Convenciones

### Backend
- Rutas en `api/routes/` organizadas por dominio (publications, journals, auth)
- Schemas Pydantic en `schemas.py`
- Lógica de negocio en `services/` (nunca en routes)
- SQLAlchemy 2.0 con async session

### Frontend (Vue 3)
- Composition API SIEMPRE (`<script setup lang="ts">`)
- Composables para lógica reutilizable (`use` prefix)
- Pinia para estado global
- Tailwind para estilos (sin CSS modules)
- Tipos explícitos en todas las funciones

### Imports de tipos en Vue/Vite
```typescript
// CORRECTO
import type { Publication } from '@/types/publication'
import { usePublicationsStore } from '@/stores/publications'

// INCORRECTO (runtime crash)
import { Publication } from '@/types/publication'
```

## API Documentación

Con backend corriendo:
- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Reglas de Desarrollo

Ver `.claude/rules/` para guías completas de:
- `common/security.md` — no secrets hardcodeados, validación inputs
- `common/coding-style.md` — inmutabilidad, archivos pequeños
- `common/testing.md` — 80% coverage mínimo
- `python/` — patrones Python específicos
- `typescript/` — patrones TypeScript/Vue
