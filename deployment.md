# Guía de Despliegue — CECAN Platform

## Entorno de Producción
La plataforma está optimizada para ejecutarse en una infraestructura **Serverless** mediante Vercel y Supabase.

### 🏠 Vercel (Hosting)
- **Frontend:** Desplegado como un proyecto de Vite/Vue.
- **Backend:** Configurado como **Vercel Functions** (Python).
- **Configuración:** Ver el archivo `vercel.json` en la raíz del monorepo para la orquestación de rutas y reescrituras.

---

## Variables de Entorno (Secrets)
Para un despliegue exitoso, las siguientes variables deben estar configuradas en el panel de Vercel:

| Variable | Uso |
|----------|-----|
| `DATABASE_URL` | String de conexión a la BD Supabase. |
| `SUPABASE_URL` | URL de la API de Supabase. |
| `SUPABASE_KEY` | Clave de acceso (Service Role). |
| `SECRET_KEY` | Firma de tokens JWT. |

---

## Flujo de CI/CD
1.  **Push a GitHub:** Cualquier cambio en la rama `main` dispara un build automático.
2.  **Generación de Build:** Vercel compila el frontend (Vite) y prepara los entornos virtuales de Python.
3.  **Despliegue Atómico:** Si los tests pasan y el build es exitoso, el nuevo código entra en producción instantáneamente.

---

## Mantenimiento de Base de Datos
Para aplicar cambios en el esquema (Migration), se deben ejecutar los scripts ubicados en `/scripts` directamente en el editor SQL de Supabase:
```bash
# Ejemplo de actualización de esquema:
cat backend/schema.sql | (Copiar y pegar en Supabase SQL Editor)
```
