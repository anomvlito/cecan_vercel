<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Search, X, ChevronLeft, ChevronRight, Users, Loader2 } from 'lucide-vue-next'
import { researchersApi } from '@/services/api'
import type { Researcher } from '@/types/publication'

const searchInput = ref('')
const searchCommitted = ref('')
const selectedType = ref<string>('')

const researchers = ref<Researcher[]>([])
const total = ref(0)
const pages = ref(0)
const page = ref(1)
const limit = 50
const loading = ref(false)
const error = ref<string | null>(null)

let debounceTimer: ReturnType<typeof setTimeout> | null = null
watch(searchInput, (val) => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    searchCommitted.value = val
    page.value = 1
  }, 400)
})

async function fetchResearchers(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const res = await researchersApi.search({
      q: searchCommitted.value || undefined,
      member_type: selectedType.value || undefined,
      page: page.value,
      limit,
    })
    researchers.value = res.items
    total.value = res.total
    pages.value = res.pages
  } catch {
    error.value = 'No se pudieron cargar los investigadores'
  } finally {
    loading.value = false
  }
}

watch([searchCommitted, selectedType, page], fetchResearchers, { immediate: true })

function setType(t: string): void {
  selectedType.value = selectedType.value === t ? '' : t
  page.value = 1
}

function clearFilters(): void {
  searchInput.value = ''
  searchCommitted.value = ''
  selectedType.value = ''
  page.value = 1
}

const hasActiveFilters = computed(() => searchCommitted.value !== '' || selectedType.value !== '')

function goTo(p: number): void {
  if (p < 1 || p > pages.value) return
  page.value = p
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const pageWindow = computed<(number | '…')[]>(() => {
  const tot = pages.value
  const cur = page.value
  if (tot <= 7) return Array.from({ length: tot }, (_, i) => i + 1)
  const items: (number | '…')[] = [1]
  if (cur > 3) items.push('…')
  for (let i = Math.max(2, cur - 1); i <= Math.min(tot - 1, cur + 1); i++) items.push(i)
  if (cur < tot - 2) items.push('…')
  items.push(tot)
  return items
})

const memberTypes = [
  { key: 'researcher', label: 'Investigador' },
  { key: 'staff', label: 'Staff' },
]

const typeColors: Record<string, string> = {
  researcher: 'bg-blue-100 text-blue-800',
  staff: 'bg-purple-100 text-purple-800',
  pi: 'bg-green-100 text-green-800',
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="bg-white border-b border-gray-200 px-4 md:px-6 py-4 sticky top-0 z-10">
      <div class="flex items-center justify-between gap-4 mb-4 flex-wrap">
        <div class="flex items-center gap-2">
          <Users class="w-5 h-5 text-blue-600" />
          <h1 class="text-xl font-bold text-gray-900">Investigadores</h1>
          <span v-if="!loading" class="ml-2 text-sm text-gray-400">
            {{ total.toLocaleString('es-CL') }} miembros
          </span>
        </div>
        <div class="relative flex-1 min-w-[200px] max-w-lg">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          <input
            v-model="searchInput"
            type="text"
            placeholder="Buscar por nombre, email o institución…"
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

      <div class="flex flex-wrap items-center gap-2">
        <span class="text-xs font-medium text-gray-500">Tipo</span>
        <button
          v-for="t in memberTypes"
          :key="t.key"
          class="px-3 py-1 text-xs font-semibold rounded-full border transition-all"
          :class="
            selectedType === t.key
              ? 'bg-blue-600 text-white border-blue-600'
              : 'border-gray-200 text-gray-500 hover:border-gray-400'
          "
          @click="setType(t.key)"
        >
          {{ t.label }}
        </button>
        <button
          v-if="hasActiveFilters"
          class="ml-auto flex items-center gap-1 text-xs text-red-500 hover:text-red-700 transition-colors"
          @click="clearFilters"
        >
          <X class="w-3 h-3" /> Limpiar
        </button>
      </div>
    </div>

    <!-- Contenido -->
    <div class="flex-1 overflow-auto">
      <div v-if="error" class="flex items-center justify-center h-64 text-red-500">{{ error }}</div>

      <div v-else-if="loading && researchers.length === 0" class="px-6 py-4">
        <div v-for="i in 10" :key="i" class="h-16 mb-2 rounded bg-gray-100 animate-pulse" :style="{ opacity: 1 - i * 0.08 }" />
      </div>

      <div v-else-if="!loading && researchers.length === 0" class="flex flex-col items-center justify-center h-64 text-gray-400">
        <Users class="w-10 h-10 mb-3 opacity-30" />
        <p class="font-medium">Sin resultados</p>
      </div>

      <!-- Tabla desktop -->
      <table v-else class="w-full text-sm hidden md:table">
        <thead class="bg-gray-50 border-b border-gray-200 sticky top-0">
          <tr>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Nombre</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-32">Tipo</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Institución</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-32">ORCID</th>
            <th class="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-16">H-index</th>
            <th class="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-24">Citas</th>
            <th class="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-20">Obras</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="r in researchers" :key="r.id" class="hover:bg-blue-50/40 transition-colors">
            <td class="px-4 py-3">
              <p class="font-medium text-gray-900">{{ r.full_name }}</p>
              <p v-if="r.email" class="text-xs text-gray-400">{{ r.email }}</p>
            </td>
            <td class="px-4 py-3">
              <span
                v-if="r.member_type"
                class="inline-block px-2 py-0.5 text-xs font-semibold rounded-full"
                :class="typeColors[r.member_type] ?? 'bg-gray-100 text-gray-600'"
              >
                {{ r.member_type }}
              </span>
            </td>
            <td class="px-4 py-3 text-xs text-gray-600 max-w-[14rem] truncate" :title="r.institution ?? undefined">
              {{ r.institution ?? '—' }}
            </td>
            <td class="px-4 py-3 font-mono text-xs text-gray-500">{{ r.orcid ?? '—' }}</td>
            <td class="px-4 py-3 text-right">
              <span v-if="r.indice_h" class="font-semibold text-blue-700">{{ r.indice_h }}</span>
              <span v-else class="text-gray-300 text-xs">—</span>
            </td>
            <td class="px-4 py-3 text-right text-gray-600">
              {{ r.citaciones_totales != null ? r.citaciones_totales.toLocaleString('es-CL') : '—' }}
            </td>
            <td class="px-4 py-3 text-right text-gray-500">{{ r.works_count ?? '—' }}</td>
          </tr>
        </tbody>
      </table>

      <!-- Cards mobile -->
      <div v-if="researchers.length > 0" class="md:hidden divide-y divide-gray-100">
        <div v-for="r in researchers" :key="r.id" class="px-4 py-3 bg-white">
          <div class="flex items-start justify-between gap-2">
            <div class="flex-1 min-w-0">
              <p class="font-medium text-gray-900 truncate">{{ r.full_name }}</p>
              <p v-if="r.email" class="text-xs text-gray-400 truncate">{{ r.email }}</p>
              <p v-if="r.institution" class="text-xs text-gray-500 mt-0.5 truncate">{{ r.institution }}</p>
            </div>
            <span
              v-if="r.member_type"
              class="flex-shrink-0 px-2 py-0.5 text-xs font-semibold rounded-full"
              :class="typeColors[r.member_type] ?? 'bg-gray-100 text-gray-600'"
            >
              {{ r.member_type }}
            </span>
          </div>
          <div class="flex gap-4 mt-2 text-xs text-gray-500">
            <span v-if="r.indice_h">H: <strong class="text-blue-700">{{ r.indice_h }}</strong></span>
            <span v-if="r.citaciones_totales">Citas: {{ r.citaciones_totales.toLocaleString('es-CL') }}</span>
            <span v-if="r.works_count">Obras: {{ r.works_count }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Paginación -->
    <div v-if="pages > 1" class="bg-white border-t border-gray-200 px-4 md:px-6 py-3 flex items-center justify-between">
      <span class="text-xs text-gray-500 hidden sm:block">
        {{ (page - 1) * limit + 1 }}–{{ Math.min(page * limit, total) }} de {{ total.toLocaleString('es-CL') }}
      </span>
      <div class="flex items-center gap-1 mx-auto sm:mx-0">
        <button class="p-1.5 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed" :disabled="page === 1" @click="goTo(page - 1)">
          <ChevronLeft class="w-4 h-4" />
        </button>
        <template v-for="(p, i) in pageWindow" :key="i">
          <span v-if="p === '…'" class="px-1 text-gray-400 text-sm">…</span>
          <button v-else class="min-w-[2rem] h-8 px-2 rounded-lg text-sm transition-colors" :class="p === page ? 'bg-blue-600 text-white font-semibold' : 'text-gray-600 hover:bg-gray-100'" @click="goTo(p)">{{ p }}</button>
        </template>
        <button class="p-1.5 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed" :disabled="page === pages" @click="goTo(page + 1)">
          <ChevronRight class="w-4 h-4" />
        </button>
      </div>
      <Loader2 v-if="loading" class="w-4 h-4 animate-spin text-blue-500 hidden sm:block" />
      <div v-else class="w-4 hidden sm:block" />
    </div>
  </div>
</template>
