# Guía de Usuario — CECAN Platform

---

## Navegación

El sidebar izquierdo da acceso a todas las secciones:

| Sección | Ruta | Función |
|---------|------|---------|
| 🗺️ Mapa 3D | `/` | Visualización espacial de publicaciones por cluster |
| 📄 Publicaciones | `/publications` | Tabla con métricas JCR, filtros y upload |
| 📤 Subir PDF | `/upload` | Subida simple de uno o varios PDFs |
| 📚 Revistas JCR | `/journals` | Búsqueda en catálogo JCR de 35.000+ revistas |
| 👥 Investigadores | `/researchers` | Directorio de investigadores con métricas |
| 🎓 Estudiantes | `/students` | Estudiantes y tesistas del centro |
| 🗂️ Proyectos | `/projects` | Proyectos científicos activos |
| 🔗 Mapa Colaboración | `/collaboration-map` | Grafo de redes de colaboración |
| 📊 Planificación | `/gantt` | Gantt interactivo por proyecto o global |
| ✅ Mis Tareas | `/my-tasks` | Actividades asignadas vía RACI |

---

## Cómo subir una publicación

### Opción 1: Drag & Drop en Publicaciones

1. Ir a `/publications`
2. Arrastrar uno o más PDFs sobre la página
3. El sistema extrae el DOI automáticamente
4. Si encuentra la revista en JCR → muestra cuartil, IF y percentil en verde
5. Si no encuentra → se puede ingresar el DOI manualmente

### Opción 2: Botón "Subir PDF"

1. Ir a `/publications` o `/upload`
2. Click en "Subir PDF"
3. Seleccionar el archivo PDF
4. Mismo proceso que drag & drop

### Opción 3: DOI manual

1. Click en "Ingresar DOI"
2. Escribir el DOI en formato `10.xxxx/yyyy`
3. El sistema consulta OpenAlex y busca la revista en JCR

---

## Interpretar los resultados

### Notificaciones de upload

| Color | Significado |
|-------|-------------|
| 🟢 Verde | Revista encontrada en JCR con métricas |
| 🟦 Azul | DOI encontrado pero revista no en base JCR local |
| 🟡 Amarillo | No se detectó DOI en el PDF |
| 🔴 Rojo | Error al procesar |

### Indicadores en la tabla

| Indicador | Significado |
|-----------|-------------|
| `Q1` verde | Cuartil 1 — mejor cuartil posible |
| `Q2` azul | Cuartil 2 |
| `Q3` amarillo | Cuartil 3 |
| `Q4` rojo | Cuartil 4 |
| `★ Top 10%` | JIF Percentil ≥ 90 |

---

## Modo Leyendas Guía

En la parte inferior del sidebar hay un botón **"Activar leyendas guía"**.

Al activarlo, aparecen etiquetas azules sobre todos los controles interactivos explicando para qué sirven. Útil para nuevos usuarios.

Click en "Desactivar leyendas" para ocultarlas.

---

## Gantt — Planificación de proyectos

### Vista por proyecto

1. Ir a `/gantt`
2. Seleccionar un proyecto del dropdown
3. El Gantt carga las actividades automáticamente

**Interacciones disponibles:**
- **Arrastrar** una barra → cambia las fechas de la actividad
- **Click** en una barra → abre modal de estado/progreso
- **Botones expandir/contraer** → controlan el nivel de detalle
- **Nueva actividad** → formulario inline para agregar tarea

### Vista global

Cambia al tab "Vista global" para ver todos los proyectos en una línea de tiempo por año. Útil para detectar solapamientos y cuellos de botella.

---

## RACI — Asignar responsabilidades

Al hacer hover sobre una actividad en el Gantt, aparecen dos íconos:

- 👥 **Responsables RACI** → abre panel para asignar miembros
- 🗑️ **Eliminar** → borra la actividad (pide confirmación)

**Roles RACI:**

| Rol | Descripción |
|-----|-------------|
| **R** — Responsible | Quien ejecuta la actividad |
| **A** — Accountable | Quien responde por el resultado |
| **C** — Consulted | Quien aporta input o expertise |
| **I** — Informed | Quien recibe actualizaciones |

---

## Mis Tareas

En `/my-tasks` se muestran todas las actividades en las que el usuario tiene una asignación RACI, con indicador de vencimiento para actividades atrasadas.

---

## Mapa 3D — Navegación

| Acción | Resultado |
|--------|-----------|
| Click + arrastrar | Rota el mapa |
| Scroll | Acerca/aleja |
| Slider zoom | Acerca/aleja suavemente |
| Hover sobre punto | Muestra tooltip con datos del paper |
| Click en cluster (leyenda) | Muestra/oculta ese cluster |
