<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Search, X, ChevronLeft, ChevronRight, FolderOpen, Loader2 } from 'lucide-vue-next'
import { projectsApi } from '@/services/api'
import type { ScientificProject } from '@/types/publication'
import GuideLabel from '@/components/ui/GuideLabel.vue'

const searchInput = ref('')
const searchCommitted = ref('')
const selectedStatus = ref<string>('')

const projects = ref<ScientificProject[]>([])
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

async function fetchProjects(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const res = await projectsApi.search({
      q: searchCommitted.value || undefined,
      status: selectedStatus.value || undefined,
      page: page.value,
      limit,
    })
    projects.value = res.items
    total.value = res.total
    pages.value = res.pages
  } catch {
    error.value = 'No se pudieron cargar los proyectos'
  } finally {
    loading.value = false
  }
}

watch([searchCommitted, selectedStatus, page], fetchProjects, { immediate: true })

function setStatus(s: string): void {
  selectedStatus.value = selectedStatus.value === s ? '' : s
  page.value = 1
}

function clearFilters(): void {
  searchInput.value = ''
  searchCommitted.value = ''
  selectedStatus.value = ''
  page.value = 1
}

const hasActiveFilters = computed(() => searchCommitted.value !== '' || selectedStatus.value !== '')

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

const statuses = ['Activo', 'Finalizado', 'En pausa', 'Pendiente']

const statusColors: Record<string, string> = {
  Activo: 'bg-green-100 text-green-800',
  Finalizado: 'bg-blue-100 text-blue-800',
  'En pausa': 'bg-yellow-100 text-yellow-800',
  Pendiente: 'bg-gray-100 text-gray-600',
}

function fmtCurrency(val: number | null, currency: string | null): string {
  if (val == null) return '—'
  return new Intl.NumberFormat('es-CL', {
    style: 'currency',
    currency: currency ?? 'CLP',
    maximumFractionDigits: 0,
  }).format(val)
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="bg-white border-b border-gray-200 px-4 md:px-6 py-4 sticky top-0 z-10">
      <div class="flex items-center justify-between gap-4 mb-4 flex-wrap">
        <div class="flex items-center gap-2">
          <FolderOpen class="w-5 h-5 text-blue-600" />
          <h1 class="text-xl font-bold text-gray-900">Proyectos Científicos</h1>
          <span v-if="!loading" class="ml-2 text-sm text-gray-400">
            {{ total.toLocaleString('es-CL') }} proyectos
          </span>
        </div>
        <GuideLabel text="Busca proyectos por nombre, código o investigador responsable" position="bottom">
          <div class="relative flex-1 min-w-[200px] max-w-lg">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            <input
              v-model="searchInput"
              type="text"
              placeholder="Buscar por título, código o investigador…"
              class="w-full pl-9 pr-9 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button v-if="searchInput" class="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600" @click="searchInput = ''; searchCommitted = ''; page = 1">
              <X class="w-4 h-4" />
            </button>
          </div>
        </GuideLabel>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <span class="text-xs font-medium text-gray-500">Estado</span>
        <GuideLabel text="Filtra proyectos por estado: Activo, Finalizado, En pausa o Pendiente" position="bottom">
          <div class="flex flex-wrap gap-2">
            <button
              v-for="s in statuses" :key="s"
              class="px-3 py-1 text-xs font-semibold rounded-full border transition-all"
              :class="selectedStatus === s ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-200 text-gray-500 hover:border-gray-400'"
              @click="setStatus(s)"
            >{{ s }}</button>
          </div>
        </GuideLabel>
        <button v-if="hasActiveFilters" class="ml-auto flex items-center gap-1 text-xs text-red-500 hover:text-red-700" @click="clearFilters">
          <X class="w-3 h-3" /> Limpiar
        </button>
      </div>
    </div>

    <!-- Contenido -->
    <div class="flex-1 overflow-auto">
      <div v-if="error" class="flex items-center justify-center h-64 text-red-500">{{ error }}</div>

      <div v-else-if="loading && projects.length === 0" class="px-6 py-4">
        <div v-for="i in 6" :key="i" class="h-20 mb-2 rounded bg-gray-100 animate-pulse" :style="{ opacity: 1 - i * 0.12 }" />
      </div>

      <div v-else-if="!loading && projects.length === 0" class="flex flex-col items-center justify-center h-64 text-gray-400">
        <FolderOpen class="w-10 h-10 mb-3 opacity-30" />
        <p class="font-medium">Sin resultados</p>
      </div>

      <!-- Tabla desktop -->
      <table v-else class="w-full text-sm hidden md:table">
        <thead class="bg-gray-50 border-b border-gray-200 sticky top-0">
          <tr>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Proyecto</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-32">Código</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-40">Investigador Principal</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-32">Fondo</th>
            <th class="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-20">Estado</th>
            <th class="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-16">Avance</th>
            <th class="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-32">Presupuesto</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="p in projects" :key="p.id" class="hover:bg-blue-50/40 transition-colors">
            <td class="px-4 py-3">
              <p class="font-medium text-gray-900 leading-tight">{{ p.title }}</p>
              <p v-if="p.work_package" class="text-xs text-gray-400 mt-0.5">{{ p.work_package }}</p>
            </td>
            <td class="px-4 py-3 font-mono text-xs text-gray-600">{{ p.code ?? '—' }}</td>
            <td class="px-4 py-3 text-xs text-gray-600 truncate max-w-[10rem]" :title="p.pi_name ?? undefined">{{ p.pi_name ?? '—' }}</td>
            <td class="px-4 py-3 text-xs text-gray-600">{{ p.grant_type ?? '—' }}</td>
            <td class="px-4 py-3 text-center">
              <span v-if="p.status" class="inline-block px-2 py-0.5 text-xs font-semibold rounded-full" :class="statusColors[p.status] ?? 'bg-gray-100 text-gray-600'">
                {{ p.status }}
              </span>
            </td>
            <td class="px-4 py-3 text-right">
              <template v-if="p.progress != null">
                <div class="flex items-center justify-end gap-1.5">
                  <div class="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div class="h-full rounded-full bg-blue-500" :style="{ width: `${p.progress}%` }" />
                  </div>
                  <span class="text-xs tabular-nums text-gray-600">{{ p.progress.toFixed(0) }}%</span>
                </div>
              </template>
              <span v-else class="text-gray-300 text-xs">—</span>
            </td>
            <td class="px-4 py-3 text-right text-xs text-gray-600">
              {{ fmtCurrency(p.budget_allocated, p.currency) }}
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Cards mobile -->
      <div v-if="projects.length > 0" class="md:hidden divide-y divide-gray-100">
        <div v-for="p in projects" :key="p.id" class="px-4 py-3 bg-white">
          <div class="flex items-start justify-between gap-2 mb-1">
            <p class="font-medium text-gray-900 flex-1 min-w-0">{{ p.title }}</p>
            <span v-if="p.status" class="flex-shrink-0 px-2 py-0.5 text-xs font-semibold rounded-full" :class="statusColors[p.status] ?? 'bg-gray-100 text-gray-600'">{{ p.status }}</span>
          </div>
          <div class="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-gray-500">
            <span v-if="p.code">{{ p.code }}</span>
            <span v-if="p.pi_name">PI: {{ p.pi_name }}</span>
            <span v-if="p.grant_type">{{ p.grant_type }}</span>
          </div>
          <div v-if="p.progress != null" class="mt-2 flex items-center gap-2">
            <div class="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full rounded-full bg-blue-500" :style="{ width: `${p.progress}%` }" />
            </div>
            <span class="text-xs text-gray-500">{{ p.progress.toFixed(0) }}%</span>
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
