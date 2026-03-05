# Documentación CECAN Vercel

Plataforma para gestión de publicaciones científicas con métricas JCR.

## Índice

| Documento | Contenido |
|-----------|-----------|
| [arquitectura.md](./arquitectura.md) | Stack, estructura del monorepo, diagrama general |
| [flujo-upload.md](./flujo-upload.md) | Pipeline de upload: extracción de DOI, vinculación JCR, casos del frontend |
| [api.md](./api.md) | Endpoints REST, parámetros, respuestas, códigos de error |
| [base-de-datos.md](./base-de-datos.md) | Esquema de tablas `journals` y `publications`, lógica de cuartiles |
| [frontend.md](./frontend.md) | Vistas, componentes, composables, types |

## Inicio Rápido

```bash
# Backend
cd backend
python -m uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm run dev

# Ambos (desde raíz)
make dev
```

## Casos de uso principales

1. **Subir un PDF** → `/upload` o drag & drop en `/publications`
2. **Ingresar DOI manualmente** → cuando el PDF no tiene DOI embebido
3. **Ver métricas JCR** → tabla en `/publications` con cuartil, IF, top 10%
4. **Auditar revistas sin métricas** → notificación indigo cuando el DOI existe pero la revista no está en la base JCR local
