# Frontend — Guía de Componentes y Vistas

Vue 3 + Vite + TypeScript + Tailwind CSS 4.
Convención: siempre Composition API con `<script setup lang="ts">`.

---

## Vistas (router-level)

### `/upload` — `UploadView.vue`

Vista dedicada para subir publicaciones. Siempre muestra la DropZone (nunca se oculta), permitiendo subir más archivos mientras se procesan los anteriores.

**Estado manejado localmente:** array de `UploadJob[]` (no en Pinia).

**Flujo:**
1. Usuario suelta o selecciona PDFs → `DropZone` emite `filesSelected`
2. Por cada archivo se crea un job y se llama `POST /publications/upload`
3. Cada job muestra su tarjeta de notificación con el resultado
4. Las notificaciones de éxito y error se auto-dismissean; las de auditoría permanecen

### `/publications` — `PublicationsView.vue`

Vista principal con tabla de publicaciones + drag & drop global sobre la página.

**Funcionalidades:**
- Listado con filtros (búsqueda, año, cuartil) y sorting por columnas
- Drag & drop en cualquier parte de la página (no solo la DropZone)
- Botón "Subir PDF" con input múltiple
- Notificaciones por job (mismo sistema que UploadView)
- Modal de DOI manual para publicaciones sin DOI en la tabla

---

## Componentes

### `DropZone.vue`

Área de arrastrar y soltar archivos PDF.

**Props:** ninguna

**Emits:**
```typescript
filesSelected: [files: File[]]
```
Emite un array de archivos PDF válidos. Filtra automáticamente archivos no-PDF.

**Características:**
- Acepta múltiples archivos (`multiple` en el input)
- Acepta drop y click
- Valida extensión `.pdf` antes de emitir
- Resetea el input después de cada selección (permite re-seleccionar el mismo archivo)

### `components/publications/ManualDoiModal.vue`

Modal para ingresar DOI manualmente en publicaciones existentes (desde la tabla de PublicationsView).

**Props:**
```typescript
publication: Publication  // la publicación a enriquecer
```

**Emits:**
```typescript
done: [result: UploadResult]
close: []
```

### `components/ui/MetricCard.vue`

Tarjeta para mostrar una métrica individual (IF, cuartil, percentil, etc.).

### `components/ui/InfoRow.vue`

Fila de información etiqueta + valor para paneles de detalle.

### `components/layout/Sidebar.vue`

Barra lateral de navegación. Rutas definidas internamente.

---

## Composables

### `composables/useUploadPdf.ts`

Encapsula el estado de upload de un único archivo (idle/uploading/success/error).

> **Nota:** `UploadView` y `PublicationsView` manejan múltiples jobs directamente con arrays de `UploadJob[]`. Este composable queda disponible para casos donde se necesita el flujo de un solo archivo.

```typescript
const { state, result, error, progress, upload, reset } = useUploadPdf()
```

---

## Types (`types/publication.ts`)

```typescript
interface Publication {
  id: number
  title: string | null
  doi: string | null
  year: number | null
  status: string
  quartile_snapshot: string | null
  impact_factor_snapshot: number | null
  jif_percentile_snapshot: number | null
  is_top10: boolean
  journal: Journal | null
  // ...
}

interface UploadResult {
  publication: Publication
  doi_found: boolean
  doi: string | null
  doi_method: string | null
  journal_found: boolean
  journal: Journal | null
  message: string
}

interface UploadJob {
  id: string
  filename: string
  state: 'uploading' | 'success' | 'error'
  result: UploadResult | null
  error: string | null
  manualDoi: string       // binding del input DOI manual
  enriching: boolean      // spinner del botón Enriquecer
}

const QUARTILE_COLORS: Record<string, string>  // clases Tailwind por cuartil
```

---

## Servicios (`services/api.ts`)

Capa axios centralizada. Funciones principales:

```typescript
publicationsApi.getAll(): Promise<Publication[]>
publicationsApi.uploadPdf(file: File, doi?: string): Promise<UploadResult>
publicationsApi.enrichWithDoi(id: number, doi: string): Promise<UploadResult>
```

---

## Sistema de notificaciones de Upload

Ver [flujo-upload.md](./flujo-upload.md#comportamiento-del-frontend) para la descripción completa de los 4 casos.

Resumen de auto-dismiss:

| Caso | Auto-dismiss |
|------|-------------|
| Éxito + revista encontrada | 4 segundos |
| Error | 5 segundos |
| Sin DOI (input manual) | No (requiere acción) |
| DOI encontrado, revista no en JCR | No (requiere revisión) |

El timer se cancela si el usuario cierra la notificación manualmente antes de que expire.
