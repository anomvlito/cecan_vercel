# Frontend Reference — CECAN Platform

## Tecnologías
- **Framework:** [Vue 3](https://vuejs.org/) con Composition API.
- **Build Tool:** [Vite](https://vitejs.org/).
- **State Management:** [Pinia](https://pinia.vuejs.org/).
- **Routing:** [Vue Router](https://router.vuejs.org/).
- **Estilos:** [Tailwind CSS](https://tailwindcss.com/) + Headless UI.
- **Visualización:** [Three.js](https://threejs.org/) (3D Force-Graph) e [D3.js](https://d3js.org/) (2D Networks).
- **Gantt:** [Frappe Gantt](https://frappe.io/gantt).

---

## Estructura de Vistas

| Ruta | Componente | Descripción |
|------|------------|-------------|
| `/` | `LandingView` | Acceso público con visión general del centro. |
| `/login` | `LoginView` | Autenticación vía Supabase Auth. |
| `/map` | `HomeView` | Mapa interactivo 3D de publicaciones (Embeddings). |
| `/publications` | `PublicationsView` | Tabla avanzada con filtros JCR y búsqueda. |
| `/upload` | `UploadView` | Interfaz de carga para PDFs y DOIs. |
| `/collaboration-map` | `CollaborationMapView` | Grafos de redes de co-autoría. |
| `/gantt` | `GanttView` | Planificación de hitos y proyectos. |

---

## Sistema de Navegación y Guardias
El `router/index.ts` gestiona la protección de rutas mediante metadatos.
- Las rutas privadas requieren un `cecan_token` válido en `localStorage`.
- Si un usuario no autenticado intenta acceder a una ruta privada, es redirigido automáticamente a `/login`.

---

## Stores (Pinia)
1. **`auth.ts`:** Gestiona el estado de la sesión, el token JWT y los datos del perfil.
2. **`guide.ts`:** Controla el estado del "Guided Tour" (UX) a través de la aplicación.
3. **`publication.ts`:** Caché reactiva de la producción científica para optimizar la carga entre vistas.
