# API Reference — CECAN Platform

## Información General
La API está construida con **FastAPI** y sigue los principios REST. Todas las respuestas son en formato JSON.

**Base URL:** `https://cecan.vercel.app/api` (Producción) o `http://localhost:8000/api` (Local).

---

## Autenticación
La mayoría de los endpoints requieren un token JWT en el header de la solicitud:
`Authorization: Bearer <TU_TOKEN_JWT>`

---

## Endpoints Principales

### 1. Publicaciones (`/publications`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/upload` | Sube un PDF o ingresa un DOI. Extrae metadatos automáticamente. |
| `GET` | `/` | Lista todas las publicaciones con sus métricas JCR. |
| `GET` | `/{id}` | Detalle de una publicación específica. |
| `DELETE`| `/{id}` | Elimina una publicación. |

### 2. Investigadores (`/researchers`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/` | Lista el capital humano del centro. |
| `GET` | `/{id}` | Perfil detallado y red de colaboración. |

### 3. Planificación / Gantt (`/gantt`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/` | Obtiene el cronograma completo de actividades. |
| `PATCH`| `/{activity_id}` | Actualiza el estado (To Do, In Progress, Done). |

---

## Documentación Interactiva
La plataforma genera automáticamente documentación interactiva accesible en:
- **Swagger UI:** `/docs`
- **ReDoc:** `/redoc`
