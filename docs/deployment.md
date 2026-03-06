# Despliegue

---

## Arquitectura de despliegue en Vercel

```mermaid
graph TD
    GH["GitHub\nrepositorio master"]
    GH -->|"push"| VB["Vercel Build"]

    subgraph VB["Vercel Build Pipeline"]
        direction LR
        B1["npm run build\n(frontend)"]
        B2["pip install\n(backend)"]
    end

    VB --> VD["Vercel CDN + Functions"]

    subgraph VD["Vercel CDN + Functions"]
        STATIC["Static Files\nfrontend/dist/\n(CDN global)"]
        SF["Serverless Function\nbackend/main.py\n(FastAPI)"]
    end

    VD --> DB["Supabase\nPostgreSQL"]
    VD --> STO["Supabase\nStorage (PDFs)"]
    VD --> OA["OpenAlex\nAPI externa"]
```

---

## Configuración `vercel.json`

```json
{
  "version": 2,
  "builds": [
    {
      "src": "backend/main.py",
      "use": "@vercel/python",
      "config": { "maxLambdaSize": "50mb" }
    },
    {
      "src": "frontend/package.json",
      "use": "@vercel/static-build",
      "config": { "distDir": "dist" }
    }
  ],
  "routes": [
    { "src": "/api/(.*)",               "dest": "backend/main.py"    },
    { "src": "^/(.+\\.[a-zA-Z0-9]+)$", "dest": "frontend/$1"        },
    { "src": "/(.*)",                   "dest": "frontend/index.html" }
  ]
}
```

**Nota sobre `maxLambdaSize`:** FastAPI + dependencias necesitan hasta 50MB. Vercel por defecto limita a 50MB, por lo que se especifica explícitamente.

---

## Variables de entorno en Vercel

Configurar en **Vercel Dashboard → Project → Settings → Environment Variables**:

### Backend

| Variable | Entorno | Descripción |
|----------|---------|-------------|
| `DATABASE_URL` | Production, Preview | `postgresql://user:pass@host:5432/db` |
| `SUPABASE_URL` | Production, Preview | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Production, Preview | Service role key (secreta) |
| `SECRET_KEY` | Production, Preview | Clave JWT aleatoria (32+ chars) |
| `ALGORITHM` | Production, Preview | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Production, Preview | `60` |
| `ALLOWED_ORIGINS` | Production | URL de producción |
| `ALLOWED_ORIGINS` | Preview | `*` (para previews de PR) |

### Frontend

| Variable | Entorno | Valor |
|----------|---------|-------|
| `VITE_API_URL` | Production | `https://tu-dominio.vercel.app/api` |
| `VITE_API_URL` | Preview | Se puede dejar vacío (usa `/api` relativo) |

---

## Despliegue en producción

```bash
# 1. Instalar Vercel CLI
npm i -g vercel

# 2. Login y link al proyecto
vercel login
vercel link

# 3. Desplegar a producción
vercel --prod

# O simplemente hacer push a master (si CI/CD está configurado)
git push origin master
```

---

## Desarrollo local

```bash
# Opción 1: Ambos en paralelo (Makefile)
make dev

# Opción 2: Por separado
# Terminal 1 — Backend
cd backend
source .venv/bin/activate
python -m uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
# → http://localhost:5173 (proxy /api → localhost:8000)
```

### Proxy de Vite

En `vite.config.ts`, el proxy redirige automáticamente `/api/*` al backend local:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

---

## Base de datos — Migraciones

```bash
cd backend

# Crear nueva migración
.venv/bin/alembic revision --autogenerate -m "descripción del cambio"

# Aplicar migraciones pendientes
.venv/bin/alembic upgrade head

# Ver historial
.venv/bin/alembic history

# Revertir última migración
.venv/bin/alembic downgrade -1
```

---

## Supabase Storage

Los PDFs se guardan en Supabase Storage en el bucket `publications/`. El path sigue el formato:

```
publications/{timestamp}_{filename}.pdf
```

El backend usa la `SUPABASE_KEY` (service role) para subir archivos sin restricciones de RLS.

---

## Build y verificación

```bash
# Frontend — type check + build
cd frontend
npm run type-check   # vue-tsc --build
npm run build        # vite build → dist/

# Backend — tests (si existen)
cd backend
python -m pytest tests/

# Health check post-deploy
curl https://tu-dominio.vercel.app/health
# → {"status": "ok", "version": "1.0.0"}
```

---

## Consideraciones de producción

### Cold starts

Vercel ejecuta el backend como Serverless Function. La primera invocación después de un período de inactividad puede tardar 1–3 segundos. Las siguientes son rápidas.

### NullPool obligatorio

```python
engine = create_engine(DATABASE_URL, poolclass=NullPool)
```

Con Serverless, cada invocación puede ser un proceso diferente. `NullPool` garantiza que no haya conexiones colgadas entre invocaciones.

### Tamaño del bundle frontend

El bundle actual (~2MB) incluye Three.js y DHTMLX Gantt. Para mejorar:
```typescript
// vite.config.ts — lazy loading de vistas pesadas
const HomeView = () => import('./views/HomeView.vue')
const GanttView = () => import('./views/GanttView.vue')
```

### CORS en producción

`ALLOWED_ORIGINS` debe contener exactamente la URL de producción. En local, puede usarse `*` para facilitar el desarrollo.
