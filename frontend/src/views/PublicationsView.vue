<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  Search, Upload, ExternalLink, ChevronUp, ChevronDown,
  Hash, CheckCircle, AlertTriangle, X, Loader2,
} from 'lucide-vue-next'
import { publicationsApi } from '@/services/api'
import type { Publication, UploadResult, UploadJob } from '@/types/publication'
import { QUARTILE_COLORS } from '@/types/publication'
import ManualDoiModal from '@/components/publications/ManualDoiModal.vue'

// ---------------------------------------------------------------------------
// Estado general
// ---------------------------------------------------------------------------
const publications = ref<Publication[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

// Filtros
const searchTerm = ref('')
const yearFilter = ref('')
const quartileFilter = ref('')

// Sorting
type SortKey = 'title' | 'year' | 'quartile_snapshot' | 'impact_factor_snapshot'
const sortKey = ref<SortKey>('year')
const sortAsc = ref(false)

// Modal DOI manual
const showDoiModal = ref(false)

// ---------------------------------------------------------------------------
// Upload jobs (drag & drop + notificaciones)
// ---------------------------------------------------------------------------
const jobs = ref<UploadJob[]>([])
const isDragging = ref(false)
let dragCounter = 0  // contador para evitar flicker en child elements

// ---------------------------------------------------------------------------
// Carga de datos
// ---------------------------------------------------------------------------
async function loadPublications(): Promise<void> {
  try {
    publications.value = await publicationsApi.getAll()
  } catch {
    error.value = 'No se pudieron cargar las publicaciones'
  } finally {
    loading.value = false
  }
}

onMounted(loadPublications)

// ---------------------------------------------------------------------------
// Drag & drop handlers
// ---------------------------------------------------------------------------
function onDragEnter(e: DragEvent): void {
  e.preventDefault()
  dragCounter++
  if (e.dataTransfer?.types.includes('Files')) isDragging.value = true
}

function onDragLeave(): void {
  dragCounter--
  if (dragCounter <= 0) {
    dragCounter = 0
    isDragging.value = false
  }
}

function onDragOver(e: DragEvent): void {
  e.preventDefault()
}

async function onDrop(e: DragEvent): Promise<void> {
  e.preventDefault()
  dragCounter = 0
  isDragging.value = false

  const files = Array.from(e.dataTransfer?.files ?? []).filter((f) =>
    f.name.toLowerCase().endsWith('.pdf'),
  )

  if (files.length === 0) return

  for (const file of files) {
    startUpload(file)
  }
}

async function startUpload(file: File, manualDoi?: string): Promise<void> {
  const jobId = `${Date.now()}-${Math.random()}`
  const job: UploadJob = {
    id: String(jobId),
    filename: file.name,
    state: 'uploading',
    result: null,
    error: null,
    manualDoi: '',
    enriching: false,
  }
  ;(jobs.value as UploadJob[]).unshift(job)

  try {
    const result = await publicationsApi.uploadPdf(file, manualDoi)
    updateJob(jobId, { state: 'success', result })
    // Agregar nueva publicación al inicio de la lista
    publications.value.unshift(result.publication)
  } catch (err: unknown) {
    const detail =
      (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      ?? 'Error al procesar el archivo'
    updateJob(jobId, { state: 'error', error: detail })
  }
}

function updateJob(id: string, patch: Partial<UploadJob>): void {
  const idx = jobs.value.findIndex((j) => j.id === id)
  if (idx !== -1) jobs.value[idx] = { ...jobs.value[idx], ...patch } as UploadJob
}

function dismissJob(id: string): void {
  jobs.value = jobs.value.filter((j) => j.id !== id)
}

async function enrichJob(job: UploadJob): Promise<void> {
  if (!job.result?.publication.id || !job.manualDoi.trim()) return
  updateJob(job.id, { enriching: true })
  try {
    const updated = await publicationsApi.enrichWithDoi(
      job.result.publication.id,
      job.manualDoi.trim(),
    )
    updateJob(job.id, { result: updated, enriching: false })
    // Actualizar publicación en la lista
    const idx = publications.value.findIndex((p) => p.id === updated.publication.id)
    if (idx !== -1) publications.value[idx] = updated.publication
  } catch (err: unknown) {
    const detail =
      (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      ?? 'No se pudo enriquecer con ese DOI'
    updateJob(job.id, { error: detail, enriching: false })
  }
}

// File input para el botón "Subir PDF"
const fileInputRef = ref<HTMLInputElement | null>(null)

function triggerFileInput(): void {
  fileInputRef.value?.click()
}

function onFileInputChange(e: Event): void {
  const input = e.target as HTMLInputElement
  const files = Array.from(input.files ?? []).filter((f) =>
    f.name.toLowerCase().endsWith('.pdf'),
  )
  files.forEach((f) => startUpload(f))
  input.value = ''
}

// ---------------------------------------------------------------------------
// Callback modal DOI
// ---------------------------------------------------------------------------
function onDoiModalDone(result: UploadResult): void {
  publications.value.unshift(result.publication)
  showDoiModal.value = false
}

// ---------------------------------------------------------------------------
// Opciones de filtro dinámicas
// ---------------------------------------------------------------------------
const uniqueYears = computed(() => {
  const years = publications.value
    .map((p) => p.year)
    .filter((y): y is number => y !== null)
  return [...new Set(years)].sort((a, b) => b - a)
})

// ---------------------------------------------------------------------------
// Filtrado y sorting
// ---------------------------------------------------------------------------
const filtered = computed(() => {
  let list = publications.value

  if (searchTerm.value.trim()) {
    const q = searchTerm.value.toLowerCase()
    list = list.filter(
      (p) =>
        p.title?.toLowerCase().includes(q) ||
        p.doi?.toLowerCase().includes(q) ||
        p.journal?.title?.toLowerCase().includes(q),
    )
  }

  if (yearFilter.value) {
    list = list.filter((p) => String(p.year) === yearFilter.value)
  }

  if (quartileFilter.value) {
    if (quartileFilter.value === 'none') {
      list = list.filter((p) => !p.quartile_snapshot)
    } else {
      list = list.filter((p) => p.quartile_snapshot === quartileFilter.value)
    }
  }

  list = [...list].sort((a, b) => {
    let aVal: string | number = ''
    let bVal: string | number = ''

    if (sortKey.value === 'title') {
      aVal = a.title ?? ''
      bVal = b.title ?? ''
    } else if (sortKey.value === 'year') {
      aVal = a.year ?? 0
      bVal = b.year ?? 0
    } else if (sortKey.value === 'quartile_snapshot') {
      aVal = a.quartile_snapshot ?? 'Z'
      bVal = b.quartile_snapshot ?? 'Z'
    } else if (sortKey.value === 'impact_factor_snapshot') {
      aVal = a.impact_factor_snapshot ?? -1
      bVal = b.impact_factor_snapshot ?? -1
    }

    const cmp = aVal < bVal ? -1 : aVal > bVal ? 1 : 0
    return sortAsc.value ? cmp : -cmp
  })

  return list
})

function setSort(key: SortKey): void {
  if (sortKey.value === key) {
    sortAsc.value = !sortAsc.value
  } else {
    sortKey.value = key
    sortAsc.value = key === 'title'
  }
}

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    uploaded: 'Subido',
    doi_extracted: 'DOI extraído',
    enriched: 'Enriquecido',
    complete: 'Completo',
    failed: 'Error',
  }
  return map[s] ?? s
}

function statusClass(s: string): string {
  const map: Record<string, string> = {
    uploaded: 'bg-gray-100 text-gray-600',
    doi_extracted: 'bg-blue-100 text-blue-700',
    enriched: 'bg-green-100 text-green-700',
    complete: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
  }
  return map[s] ?? 'bg-gray-100 text-gray-600'
}

function resetFilters(): void {
  searchTerm.value = ''
  yearFilter.value = ''
  quartileFilter.value = ''
}

const DOI_RE = /^10\.\d{4,9}\/[-._;()/:a-zA-Z0-9]+$/
function isValidDoi(doi: string): boolean {
  return DOI_RE.test(doi.trim())
}
</script>

<template>
  <!-- Contenedor principal con drag zone -->
  <div
    class="relative p-8 min-h-full"
    @dragenter="onDragEnter"
    @dragleave="onDragLeave"
    @dragover="onDragOver"
    @drop="onDrop"
  >
    <!-- Overlay drag -->
    <Transition name="fade">
      <div
        v-if="isDragging"
        class="absolute inset-0 z-40 bg-blue-500/10 border-4 border-dashed border-blue-400 rounded-2xl flex flex-col items-center justify-center pointer-events-none"
      >
        <Upload class="w-14 h-14 text-blue-500 mb-3" />
        <p class="text-xl font-semibold text-blue-700">Suelta el PDF para subirlo</p>
        <p class="text-sm text-blue-500 mt-1">Se procesará automáticamente</p>
      </div>
    </Transition>

    <!-- Input file oculto -->
    <input
      ref="fileInputRef"
      type="file"
      accept=".pdf"
      multiple
      class="hidden"
      @change="onFileInputChange"
    />

    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Publicaciones</h1>
        <p class="text-sm text-gray-500 mt-0.5">
          {{ filtered.length }} de {{ publications.length }} publicaciones
        </p>
      </div>
      <div class="flex items-center gap-2">
        <!-- Botón DOI manual -->
        <button
          class="flex items-center gap-2 px-4 py-2 border border-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
          @click="showDoiModal = true"
        >
          <Hash class="w-4 h-4" />
          Ingresar DOI
        </button>
        <!-- Botón subir PDF -->
        <button
          class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          @click="triggerFileInput"
        >
          <Upload class="w-4 h-4" />
          Subir PDF
        </button>
      </div>
    </div>

    <!-- Notificaciones de upload jobs -->
    <div v-if="jobs.length > 0" class="mb-4 space-y-2">
      <div
        v-for="job in jobs"
        :key="job.id"
        class="rounded-xl border px-4 py-3 flex items-start gap-3 text-sm"
        :class="{
          'bg-blue-50 border-blue-200': job.state === 'uploading',
          'bg-green-50 border-green-200': job.state === 'success' && job.result?.journal_found,
          'bg-yellow-50 border-yellow-200': job.state === 'success' && !job.result?.journal_found,
          'bg-red-50 border-red-200': job.state === 'error',
        }"
      >
        <!-- Icono de estado -->
        <Loader2
          v-if="job.state === 'uploading'"
          class="w-4 h-4 text-blue-500 animate-spin flex-shrink-0 mt-0.5"
        />
        <CheckCircle
          v-else-if="job.state === 'success' && job.result?.journal_found"
          class="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5"
        />
        <AlertTriangle
          v-else-if="job.state === 'success'"
          class="w-4 h-4 text-yellow-500 flex-shrink-0 mt-0.5"
        />
        <AlertTriangle
          v-else
          class="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5"
        />

        <!-- Contenido -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="font-medium text-gray-800 truncate max-w-xs">{{ job.filename }}</span>
            <!-- Métricas si enriquecido -->
            <span
              v-if="job.result?.publication.quartile_snapshot"
              class="inline-flex px-1.5 py-0.5 rounded-full text-xs font-semibold"
              :class="QUARTILE_COLORS[job.result.publication.quartile_snapshot] ?? 'bg-gray-100 text-gray-600'"
            >
              {{ job.result.publication.quartile_snapshot }}
            </span>
            <span
              v-if="job.result?.publication.is_top10"
              class="inline-flex px-1.5 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-700"
            >
              ★ Top 10%
            </span>
          </div>

          <!-- Mensaje de estado -->
          <p
            v-if="job.state === 'uploading'"
            class="text-xs text-blue-600 mt-0.5"
          >
            Procesando...
          </p>
          <p
            v-else-if="job.result"
            class="text-xs text-gray-500 mt-0.5"
          >
            {{ job.result.message }}
          </p>
          <p v-else-if="job.error" class="text-xs text-red-600 mt-0.5">{{ job.error }}</p>

          <!-- Input DOI manual si no se encontró DOI -->
          <div
            v-if="job.state === 'success' && !job.result?.doi_found"
            class="mt-2 flex items-center gap-2"
          >
            <input
              v-model="job.manualDoi"
              type="text"
              placeholder="Ingresa el DOI manualmente: 10.xxxx/..."
              class="flex-1 px-2 py-1 text-xs border border-yellow-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-yellow-400 font-mono bg-white"
              @keyup.enter="enrichJob(job)"
            />
            <button
              class="px-3 py-1 bg-yellow-500 text-white text-xs font-medium rounded-lg hover:bg-yellow-600 disabled:opacity-50 transition-colors flex items-center gap-1"
              :disabled="!isValidDoi(job.manualDoi) || job.enriching"
              @click="enrichJob(job)"
            >
              <Loader2 v-if="job.enriching" class="w-3 h-3 animate-spin" />
              {{ job.enriching ? '' : 'Enriquecer' }}
            </button>
          </div>

          <!-- Error del enriquecimiento -->
          <p v-if="job.error && job.state === 'success'" class="text-xs text-red-500 mt-1">
            {{ job.error }}
          </p>
        </div>

        <!-- Botón cerrar -->
        <button
          v-if="job.state !== 'uploading'"
          class="text-gray-400 hover:text-gray-600 flex-shrink-0"
          @click="dismissJob(job.id)"
        >
          <X class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Filtros -->
    <div class="bg-white rounded-xl border border-gray-200 p-4 mb-4 flex flex-wrap gap-3 items-center">
      <div class="relative flex-1 min-w-48">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          v-model="searchTerm"
          type="text"
          placeholder="Buscar por título, DOI, revista..."
          class="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <select
        v-model="yearFilter"
        class="px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
      >
        <option value="">Todos los años</option>
        <option v-for="year in uniqueYears" :key="year" :value="String(year)">{{ year }}</option>
      </select>

      <select
        v-model="quartileFilter"
        class="px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
      >
        <option value="">Todos los cuartiles</option>
        <option value="Q1">Q1</option>
        <option value="Q2">Q2</option>
        <option value="Q3">Q3</option>
        <option value="Q4">Q4</option>
        <option value="none">Sin cuartil</option>
      </select>

      <button
        v-if="searchTerm || yearFilter || quartileFilter"
        class="px-3 py-2 text-sm text-gray-500 hover:text-gray-700 underline"
        @click="resetFilters"
      >
        Limpiar
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center items-center py-24">
      <div class="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
      <p class="text-red-600 font-medium">{{ error }}</p>
    </div>

    <!-- Tabla -->
    <div v-else class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-200 bg-gray-50">
              <th
                class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide cursor-pointer select-none hover:text-gray-700"
                @click="setSort('title')"
              >
                <span class="flex items-center gap-1">
                  Título
                  <ChevronUp v-if="sortKey === 'title' && sortAsc" class="w-3 h-3" />
                  <ChevronDown v-else-if="sortKey === 'title' && !sortAsc" class="w-3 h-3" />
                </span>
              </th>
              <th
                class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide cursor-pointer select-none hover:text-gray-700 w-20"
                @click="setSort('year')"
              >
                <span class="flex items-center gap-1">
                  Año
                  <ChevronUp v-if="sortKey === 'year' && sortAsc" class="w-3 h-3" />
                  <ChevronDown v-else-if="sortKey === 'year' && !sortAsc" class="w-3 h-3" />
                </span>
              </th>
              <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Revista
              </th>
              <th
                class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide cursor-pointer select-none hover:text-gray-700 w-28"
                @click="setSort('quartile_snapshot')"
              >
                <span class="flex items-center gap-1">
                  Cuartil
                  <ChevronUp v-if="sortKey === 'quartile_snapshot' && sortAsc" class="w-3 h-3" />
                  <ChevronDown v-else-if="sortKey === 'quartile_snapshot' && !sortAsc" class="w-3 h-3" />
                </span>
              </th>
              <th
                class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide cursor-pointer select-none hover:text-gray-700 w-24"
                @click="setSort('impact_factor_snapshot')"
              >
                <span class="flex items-center gap-1">
                  IF
                  <ChevronUp v-if="sortKey === 'impact_factor_snapshot' && sortAsc" class="w-3 h-3" />
                  <ChevronDown v-else-if="sortKey === 'impact_factor_snapshot' && !sortAsc" class="w-3 h-3" />
                </span>
              </th>
              <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-32">
                DOI
              </th>
              <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-32">
                Estado
              </th>
            </tr>
          </thead>

          <tbody class="divide-y divide-gray-100">
            <tr v-if="filtered.length === 0">
              <td colspan="7" class="px-4 py-16 text-center text-gray-400">
                <p class="font-medium">No se encontraron publicaciones</p>
                <p class="text-sm mt-1">Arrastra un PDF o usa el botón "Subir PDF"</p>
              </td>
            </tr>

            <tr
              v-for="pub in filtered"
              :key="pub.id"
              class="hover:bg-gray-50 transition-colors"
            >
              <td class="px-4 py-3 max-w-xs">
                <p class="font-medium text-gray-900 truncate" :title="pub.title ?? undefined">
                  {{ pub.title ?? '—' }}
                </p>
                <p v-if="pub.pdf_filename" class="text-xs text-gray-400 truncate mt-0.5">
                  {{ pub.pdf_filename }}
                </p>
              </td>
              <td class="px-4 py-3 text-gray-600">{{ pub.year ?? '—' }}</td>
              <td class="px-4 py-3 max-w-[200px]">
                <p v-if="pub.journal" class="text-gray-700 truncate" :title="pub.journal.title">
                  {{ pub.journal.title }}
                </p>
                <p v-else-if="pub.journal_issn_raw" class="text-gray-400 text-xs">
                  ISSN: {{ pub.journal_issn_raw }}
                </p>
                <span v-else class="text-gray-300">—</span>
              </td>
              <td class="px-4 py-3">
                <div class="flex flex-col gap-1">
                  <span
                    v-if="pub.quartile_snapshot"
                    class="inline-flex px-2 py-0.5 rounded-full text-xs font-semibold w-fit"
                    :class="QUARTILE_COLORS[pub.quartile_snapshot] ?? 'bg-gray-100 text-gray-600'"
                  >
                    {{ pub.quartile_snapshot }}
                  </span>
                  <span v-else class="text-gray-300">—</span>
                  <span
                    v-if="pub.is_top10"
                    class="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-700 w-fit"
                    title="Top 10% — JIF Percentile ≥ 90"
                  >
                    ★ Top 10%
                  </span>
                </div>
              </td>
              <td class="px-4 py-3 text-gray-700 tabular-nums">
                {{ pub.impact_factor_snapshot !== null ? pub.impact_factor_snapshot.toFixed(3) : '—' }}
              </td>
              <td class="px-4 py-3">
                <a
                  v-if="pub.doi"
                  :href="`https://doi.org/${pub.doi}`"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 text-xs font-mono truncate max-w-[120px]"
                  :title="pub.doi"
                >
                  {{ pub.doi }}
                  <ExternalLink class="w-3 h-3 flex-shrink-0" />
                </a>
                <span v-else class="text-gray-300">—</span>
              </td>
              <td class="px-4 py-3">
                <span
                  class="inline-flex px-2 py-0.5 rounded-full text-xs font-medium"
                  :class="statusClass(pub.status)"
                >
                  {{ statusLabel(pub.status) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Modal DOI manual -->
  <ManualDoiModal
    v-if="showDoiModal"
    @close="showDoiModal = false"
    @done="onDoiModalDone"
  />
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
