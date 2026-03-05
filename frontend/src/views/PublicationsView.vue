<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Search, Upload, ExternalLink, ChevronUp, ChevronDown } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import { publicationsApi } from '@/services/api'
import type { Publication } from '@/types/publication'
import { QUARTILE_COLORS } from '@/types/publication'

const router = useRouter()

// --- Estado ---
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

// --- Carga de datos ---
onMounted(async () => {
  try {
    publications.value = await publicationsApi.getAll()
  } catch {
    error.value = 'No se pudieron cargar las publicaciones'
  } finally {
    loading.value = false
  }
})

// --- Opciones de filtro dinámicas ---
const uniqueYears = computed(() => {
  const years = publications.value
    .map((p) => p.year)
    .filter((y): y is number => y !== null)
  return [...new Set(years)].sort((a, b) => b - a)
})

// --- Publicaciones filtradas y ordenadas ---
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

  // Sort
  list = [...list].sort((a, b) => {
    let aVal: string | number | null = null
    let bVal: string | number | null = null

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

    if (aVal === null) aVal = ''
    if (bVal === null) bVal = ''

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

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    uploaded: 'Subido',
    doi_extracted: 'DOI extraído',
    enriched: 'Enriquecido',
    complete: 'Completo',
    failed: 'Error',
  }
  return map[status] ?? status
}

function statusClass(status: string): string {
  const map: Record<string, string> = {
    uploaded: 'bg-gray-100 text-gray-600',
    doi_extracted: 'bg-blue-100 text-blue-700',
    enriched: 'bg-green-100 text-green-700',
    complete: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
  }
  return map[status] ?? 'bg-gray-100 text-gray-600'
}

function resetFilters(): void {
  searchTerm.value = ''
  yearFilter.value = ''
  quartileFilter.value = ''
}
</script>

<template>
  <div class="p-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Publicaciones</h1>
        <p class="text-sm text-gray-500 mt-0.5">
          {{ filtered.length }} de {{ publications.length }} publicaciones
        </p>
      </div>
      <button
        class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
        @click="router.push('/upload')"
      >
        <Upload class="w-4 h-4" />
        Subir PDF
      </button>
    </div>

    <!-- Filtros -->
    <div class="bg-white rounded-xl border border-gray-200 p-4 mb-4 flex flex-wrap gap-3 items-center">
      <!-- Search -->
      <div class="relative flex-1 min-w-48">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          v-model="searchTerm"
          type="text"
          placeholder="Buscar por título, DOI, revista..."
          class="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <!-- Año -->
      <select
        v-model="yearFilter"
        class="px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
      >
        <option value="">Todos los años</option>
        <option v-for="year in uniqueYears" :key="year" :value="String(year)">
          {{ year }}
        </option>
      </select>

      <!-- Cuartil -->
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

      <!-- Reset -->
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
              <!-- Título -->
              <th
                class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide cursor-pointer select-none hover:text-gray-700"
                @click="setSort('title')"
              >
                <span class="flex items-center gap-1">
                  Título
                  <ChevronUp
                    v-if="sortKey === 'title' && sortAsc"
                    class="w-3 h-3"
                  />
                  <ChevronDown
                    v-else-if="sortKey === 'title' && !sortAsc"
                    class="w-3 h-3"
                  />
                </span>
              </th>

              <!-- Año -->
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

              <!-- Revista -->
              <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Revista
              </th>

              <!-- Cuartil -->
              <th
                class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide cursor-pointer select-none hover:text-gray-700 w-24"
                @click="setSort('quartile_snapshot')"
              >
                <span class="flex items-center gap-1">
                  Cuartil
                  <ChevronUp v-if="sortKey === 'quartile_snapshot' && sortAsc" class="w-3 h-3" />
                  <ChevronDown v-else-if="sortKey === 'quartile_snapshot' && !sortAsc" class="w-3 h-3" />
                </span>
              </th>

              <!-- IF -->
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

              <!-- DOI -->
              <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-32">
                DOI
              </th>

              <!-- Estado -->
              <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-32">
                Estado
              </th>
            </tr>
          </thead>

          <tbody class="divide-y divide-gray-100">
            <!-- Empty state -->
            <tr v-if="filtered.length === 0">
              <td colspan="7" class="px-4 py-16 text-center text-gray-400">
                <p class="font-medium">No se encontraron publicaciones</p>
                <p class="text-sm mt-1">Prueba ajustando los filtros o sube un PDF nuevo</p>
              </td>
            </tr>

            <!-- Filas -->
            <tr
              v-for="pub in filtered"
              :key="pub.id"
              class="hover:bg-gray-50 transition-colors"
            >
              <!-- Título -->
              <td class="px-4 py-3 max-w-xs">
                <p class="font-medium text-gray-900 truncate" :title="pub.title ?? undefined">
                  {{ pub.title ?? '—' }}
                </p>
                <p v-if="pub.pdf_filename" class="text-xs text-gray-400 truncate mt-0.5">
                  {{ pub.pdf_filename }}
                </p>
              </td>

              <!-- Año -->
              <td class="px-4 py-3 text-gray-600">
                {{ pub.year ?? '—' }}
              </td>

              <!-- Revista -->
              <td class="px-4 py-3 max-w-[200px]">
                <p v-if="pub.journal" class="text-gray-700 truncate" :title="pub.journal.title">
                  {{ pub.journal.title }}
                </p>
                <p v-else-if="pub.journal_issn_raw" class="text-gray-400 text-xs">
                  ISSN: {{ pub.journal_issn_raw }}
                </p>
                <span v-else class="text-gray-300">—</span>
              </td>

              <!-- Cuartil -->
              <td class="px-4 py-3">
                <span
                  v-if="pub.quartile_snapshot"
                  class="inline-flex px-2 py-0.5 rounded-full text-xs font-semibold"
                  :class="QUARTILE_COLORS[pub.quartile_snapshot] ?? 'bg-gray-100 text-gray-600'"
                >
                  {{ pub.quartile_snapshot }}
                </span>
                <span v-else class="text-gray-300">—</span>
              </td>

              <!-- IF -->
              <td class="px-4 py-3 text-gray-700 tabular-nums">
                {{ pub.impact_factor_snapshot !== null ? pub.impact_factor_snapshot.toFixed(3) : '—' }}
              </td>

              <!-- DOI -->
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

              <!-- Estado -->
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
</template>
