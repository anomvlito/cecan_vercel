<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Search, X, ChevronLeft, ChevronRight, BookMarked, Loader2 } from 'lucide-vue-next'
import { journalsApi } from '@/services/api'
import type { Journal } from '@/types/publication'
import { QUARTILE_COLORS } from '@/types/publication'

// ---------------------------------------------------------------------------
// Estado de filtros
// ---------------------------------------------------------------------------
const searchInput = ref('')
const searchCommitted = ref('')
const selectedQuartiles = ref<Set<string>>(new Set())
const pctPreset = ref<'all' | '90' | '75' | '50'>('all')

// ---------------------------------------------------------------------------
// Estado de datos
// ---------------------------------------------------------------------------
const journals = ref<Journal[]>([])
const total = ref(0)
const pages = ref(0)
const page = ref(1)
const limit = 50
const loading = ref(false)
const error = ref<string | null>(null)

// ---------------------------------------------------------------------------
// Debounce del buscador
// ---------------------------------------------------------------------------
let debounceTimer: ReturnType<typeof setTimeout> | null = null

watch(searchInput, (val) => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    searchCommitted.value = val
    page.value = 1
  }, 400)
})

// ---------------------------------------------------------------------------
// Computed: parámetros derivados de los filtros
// ---------------------------------------------------------------------------
const quartileParam = computed(() =>
  selectedQuartiles.value.size > 0 ? [...selectedQuartiles.value].join(',') : undefined,
)

const minPct = computed<number | null>(() => {
  if (pctPreset.value === '90') return 90
  if (pctPreset.value === '75') return 75
  if (pctPreset.value === '50') return 50
  return null
})

// ---------------------------------------------------------------------------
// Fetch
// ---------------------------------------------------------------------------
async function fetchJournals(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const res = await journalsApi.search({
      q: searchCommitted.value || undefined,
      quartile: quartileParam.value,
      min_percentile: minPct.value,
      page: page.value,
      limit,
    })
    journals.value = res.items
    total.value = res.total
    pages.value = res.pages
  } catch {
    error.value = 'No se pudieron cargar las revistas'
  } finally {
    loading.value = false
  }
}

watch([searchCommitted, quartileParam, minPct, page], fetchJournals, { immediate: true })

// ---------------------------------------------------------------------------
// Acciones de filtros
// ---------------------------------------------------------------------------
function toggleQuartile(q: string): void {
  const next = new Set(selectedQuartiles.value)
  if (next.has(q)) next.delete(q)
  else next.add(q)
  selectedQuartiles.value = next
  page.value = 1
}

function setPctPreset(p: typeof pctPreset.value): void {
  pctPreset.value = p
  page.value = 1
}

function clearFilters(): void {
  searchInput.value = ''
  searchCommitted.value = ''
  selectedQuartiles.value = new Set()
  pctPreset.value = 'all'
  page.value = 1
}

const hasActiveFilters = computed(
  () =>
    searchCommitted.value !== '' ||
    selectedQuartiles.value.size > 0 ||
    pctPreset.value !== 'all',
)

// ---------------------------------------------------------------------------
// Paginación
// ---------------------------------------------------------------------------
function goTo(p: number): void {
  if (p < 1 || p > pages.value) return
  page.value = p
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const pageWindow = computed<(number | '…')[]>(() => {
  const total = pages.value
  const cur = page.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const items: (number | '…')[] = [1]
  if (cur > 3) items.push('…')
  for (let i = Math.max(2, cur - 1); i <= Math.min(total - 1, cur + 1); i++) items.push(i)
  if (cur < total - 2) items.push('…')
  items.push(total)
  return items
})

// ---------------------------------------------------------------------------
// Helpers de display
// ---------------------------------------------------------------------------
function fmt(n: number | null, decimals = 3): string {
  if (n == null) return '—'
  return n.toFixed(decimals)
}

function deriveQuartile(j: Journal): string | null {
  const direct = [j.quartile_rank].find((v) => v && /^Q[1-4]$/i.test(v.trim()))
  return direct?.trim().toUpperCase() ?? null
}

const pctPresets = [
  { key: 'all' as const, label: 'Todos' },
  { key: '90' as const, label: '≥ 90%' },
  { key: '75' as const, label: '≥ 75%' },
  { key: '50' as const, label: '≥ 50%' },
]

const quartileOptions = ['Q1', 'Q2', 'Q3', 'Q4']
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- ------------------------------------------------------------------ -->
    <!-- Header + buscador -->
    <!-- ------------------------------------------------------------------ -->
    <div class="bg-white border-b border-gray-200 px-6 py-4 sticky top-0 z-10">
      <div class="flex items-center justify-between gap-4 mb-4">
        <div class="flex items-center gap-2">
          <BookMarked class="w-5 h-5 text-blue-600" />
          <h1 class="text-xl font-bold text-gray-900">Revistas JCR</h1>
          <span v-if="!loading" class="ml-2 text-sm text-gray-400">
            {{ total.toLocaleString('es-CL') }} revistas
          </span>
        </div>

        <!-- Buscador -->
        <div class="relative flex-1 max-w-lg">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          <input
            v-model="searchInput"
            type="text"
            placeholder="Buscar por título, ISSN, publisher, categoría, país…"
            class="w-full pl-9 pr-9 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            v-if="searchInput"
            class="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            @click="searchInput = ''; searchCommitted = ''; page = 1"
          >
            <X class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- Filtros -->
      <div class="flex flex-wrap items-center gap-3">
        <!-- Cuartil -->
        <div class="flex items-center gap-1.5">
          <span class="text-xs font-medium text-gray-500 mr-1">Cuartil</span>
          <button
            v-for="q in quartileOptions"
            :key="q"
            class="px-3 py-1 text-xs font-semibold rounded-full border transition-all"
            :class="
              selectedQuartiles.has(q)
                ? `${QUARTILE_COLORS[q]} border-transparent ring-2 ring-offset-1 ring-current`
                : 'border-gray-200 text-gray-500 hover:border-gray-400'
            "
            @click="toggleQuartile(q)"
          >
            {{ q }}
          </button>
        </div>

        <div class="w-px h-5 bg-gray-200" />

        <!-- Percentil -->
        <div class="flex items-center gap-1.5">
          <span class="text-xs font-medium text-gray-500 mr-1">JIF Percentil</span>
          <button
            v-for="preset in pctPresets"
            :key="preset.key"
            class="px-3 py-1 text-xs font-medium rounded-full border transition-all"
            :class="
              pctPreset === preset.key
                ? 'bg-blue-600 text-white border-blue-600'
                : 'border-gray-200 text-gray-500 hover:border-gray-400'
            "
            @click="setPctPreset(preset.key)"
          >
            {{ preset.label }}
          </button>
        </div>

        <!-- Limpiar filtros -->
        <button
          v-if="hasActiveFilters"
          class="ml-auto flex items-center gap-1 text-xs text-red-500 hover:text-red-700 transition-colors"
          @click="clearFilters"
        >
          <X class="w-3 h-3" />
          Limpiar filtros
        </button>
      </div>
    </div>

    <!-- ------------------------------------------------------------------ -->
    <!-- Tabla -->
    <!-- ------------------------------------------------------------------ -->
    <div class="flex-1 overflow-auto">
      <!-- Estado de error -->
      <div v-if="error" class="flex items-center justify-center h-64 text-red-500">
        {{ error }}
      </div>

      <!-- Skeleton de carga -->
      <div v-else-if="loading && journals.length === 0" class="px-6 py-4">
        <div
          v-for="i in 12"
          :key="i"
          class="h-12 mb-2 rounded bg-gray-100 animate-pulse"
          :style="{ opacity: 1 - i * 0.06 }"
        />
      </div>

      <!-- Sin resultados -->
      <div
        v-else-if="!loading && journals.length === 0"
        class="flex flex-col items-center justify-center h-64 text-gray-400"
      >
        <BookMarked class="w-10 h-10 mb-3 opacity-30" />
        <p class="font-medium">Sin resultados</p>
        <p class="text-sm mt-1">Intenta con otros términos o cambia los filtros</p>
      </div>

      <!-- Tabla de datos -->
      <table v-else class="w-full text-sm">
        <thead class="bg-gray-50 border-b border-gray-200 sticky top-0">
          <tr>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Revista
            </th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-32">
              ISSN / eISSN
            </th>
            <th class="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-20">
              IF
            </th>
            <th class="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-20">
              IF 5yr
            </th>
            <th class="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-16">
              Cuartil
            </th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-40">
              JIF Percentil
            </th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-48">
              Publisher
            </th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Categorías
            </th>
          </tr>
        </thead>

        <tbody class="divide-y divide-gray-100">
          <tr
            v-for="j in journals"
            :key="j.id"
            class="hover:bg-blue-50/40 transition-colors group"
          >
            <!-- Título -->
            <td class="px-4 py-3">
              <p class="font-medium text-gray-900 leading-tight">{{ j.title }}</p>
              <p v-if="j.title_abbrev" class="text-xs text-gray-400 mt-0.5">{{ j.title_abbrev }}</p>
            </td>

            <!-- ISSN / eISSN -->
            <td class="px-4 py-3">
              <span class="font-mono text-xs text-gray-700 block">{{ j.issn ?? '—' }}</span>
              <span v-if="j.eissn" class="font-mono text-xs text-gray-400 block">{{ j.eissn }}</span>
            </td>

            <!-- Impact Factor -->
            <td class="px-4 py-3 text-right">
              <span
                class="font-semibold"
                :class="j.impact_factor && j.impact_factor > 10 ? 'text-blue-700' : 'text-gray-800'"
              >
                {{ fmt(j.impact_factor) }}
              </span>
            </td>

            <!-- IF 5yr -->
            <td class="px-4 py-3 text-right text-gray-500">
              {{ fmt(j.impact_factor_5yr) }}
            </td>

            <!-- Cuartil -->
            <td class="px-4 py-3 text-center">
              <span
                v-if="deriveQuartile(j)"
                class="inline-block px-2 py-0.5 text-xs font-bold rounded-full"
                :class="QUARTILE_COLORS[deriveQuartile(j)!] ?? 'bg-gray-100 text-gray-600'"
              >
                {{ deriveQuartile(j) }}
              </span>
              <span v-else class="text-gray-300 text-xs">—</span>
            </td>

            <!-- JIF Percentil con barra visual -->
            <td class="px-4 py-3">
              <template v-if="j.jif_percentile != null">
                <div class="flex items-center gap-2">
                  <div class="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      class="h-full rounded-full transition-all"
                      :class="
                        j.jif_percentile >= 90
                          ? 'bg-purple-500'
                          : j.jif_percentile >= 75
                            ? 'bg-green-500'
                            : j.jif_percentile >= 50
                              ? 'bg-blue-400'
                              : 'bg-gray-300'
                      "
                      :style="{ width: `${j.jif_percentile}%` }"
                    />
                  </div>
                  <span class="text-xs text-gray-600 w-10 text-right tabular-nums">
                    {{ j.jif_percentile.toFixed(1) }}
                  </span>
                </div>
              </template>
              <span v-else class="text-gray-300 text-xs">—</span>
            </td>

            <!-- Publisher -->
            <td class="px-4 py-3">
              <span
                class="text-xs text-gray-600 block truncate max-w-[11rem]"
                :title="j.publisher_name ?? undefined"
              >
                {{ j.publisher_name ?? '—' }}
              </span>
              <span v-if="j.country" class="text-xs text-gray-400">{{ j.country }}</span>
            </td>

            <!-- Categorías -->
            <td class="px-4 py-3">
              <span
                class="text-xs text-gray-500 line-clamp-2 leading-tight"
                :title="j.categories_description ?? undefined"
              >
                {{ j.categories_description ?? '—' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ------------------------------------------------------------------ -->
    <!-- Paginación -->
    <!-- ------------------------------------------------------------------ -->
    <div
      v-if="pages > 1"
      class="bg-white border-t border-gray-200 px-6 py-3 flex items-center justify-between"
    >
      <span class="text-xs text-gray-500">
        Mostrando {{ (page - 1) * limit + 1 }}–{{ Math.min(page * limit, total) }}
        de {{ total.toLocaleString('es-CL') }}
      </span>

      <div class="flex items-center gap-1">
        <button
          class="p-1.5 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          :disabled="page === 1"
          @click="goTo(page - 1)"
        >
          <ChevronLeft class="w-4 h-4" />
        </button>

        <template v-for="(p, i) in pageWindow" :key="i">
          <span v-if="p === '…'" class="px-1 text-gray-400 text-sm select-none">…</span>
          <button
            v-else
            class="min-w-[2rem] h-8 px-2 rounded-lg text-sm transition-colors"
            :class="
              p === page
                ? 'bg-blue-600 text-white font-semibold'
                : 'text-gray-600 hover:bg-gray-100'
            "
            @click="goTo(p)"
          >
            {{ p }}
          </button>
        </template>

        <button
          class="p-1.5 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          :disabled="page === pages"
          @click="goTo(page + 1)"
        >
          <ChevronRight class="w-4 h-4" />
        </button>
      </div>

      <!-- Spinner de carga mientras pagina -->
      <Loader2 v-if="loading" class="w-4 h-4 animate-spin text-blue-500" />
      <div v-else class="w-4" />
    </div>
  </div>
</template>
