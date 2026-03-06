<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ChevronDown, ChevronRight } from 'lucide-vue-next'
import { projectsApi, projectActivitiesApi } from '@/services/api'
import type { ScientificProject, ProjectActivity } from '@/types/publication'

// ── State ─────────────────────────────────────────────────────────────────────
const projects = ref<ScientificProject[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const selectedYear = ref(new Date().getFullYear())

// Activities per project (loaded on expand)
const activitiesMap = ref<Record<number, ProjectActivity[]>>({})
const expandedProjects = ref<Set<number>>(new Set())
const loadingActivities = ref<Set<number>>(new Set())

// ── Load projects ─────────────────────────────────────────────────────────────
onMounted(async () => {
  loading.value = true
  try {
    const res = await projectsApi.search({ limit: 200 })
    projects.value = res.items
  } catch {
    error.value = 'Error al cargar proyectos'
  } finally {
    loading.value = false
  }
})

// ── Year navigation ────────────────────────────────────────────────────────────
const availableYears = [2021, 2022, 2023, 2024, 2025, 2026]

const monthNames = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

// ── WP colors ─────────────────────────────────────────────────────────────────
const wpColors: Record<string, string> = {
  WP1: '#3b82f6',
  WP2: '#10b981',
  WP3: '#f59e0b',
  WP4: '#8b5cf6',
  WP5: '#ef4444',
}

function getWpColor(wp: string | null): string {
  if (!wp) return '#94a3b8'
  const key = wp.toUpperCase().replace(/\s+/g, '')
  return wpColors[key] ?? '#94a3b8'
}

// ── Group projects by WP ──────────────────────────────────────────────────────
const groupedProjects = computed(() => {
  const groups: Record<string, ScientificProject[]> = {}
  for (const p of projects.value) {
    const wp = p.work_package ?? 'Sin WP'
    if (!groups[wp]) groups[wp] = []
    groups[wp].push(p)
  }
  return groups
})

const totalActivities = computed(() => {
  return Object.values(activitiesMap.value).reduce((sum, acts) => sum + acts.length, 0)
})

// ── Parsea fecha ISO como hora local ──────────────────────────────────────────
function parseLocalDate(str: string | null | undefined): Date | null {
  if (!str) return null
  const d = new Date(str.split('T')[0] + 'T00:00:00')
  return isNaN(d.getTime()) ? null : d
}

// ── Bar positioning ────────────────────────────────────────────────────────────
function getProjectBar(project: ScientificProject): { left: string; width: string } | null {
  const pStart = parseLocalDate(project.start_date)
  const pEnd = parseLocalDate(project.end_date)
  if (!pStart || !pEnd) return null
  const yearStart = new Date(selectedYear.value, 0, 1)
  const yearEnd = new Date(selectedYear.value, 11, 31)
  if (pEnd < yearStart || pStart > yearEnd) return null
  const effStart = pStart < yearStart ? yearStart : pStart
  const effEnd = pEnd > yearEnd ? yearEnd : pEnd
  const left = (effStart.getMonth() / 12) * 100
  const width = Math.max(((effEnd.getMonth() - effStart.getMonth() + 1) / 12) * 100, 4)
  return { left: `${left}%`, width: `${width}%` }
}

function getActivityBar(activity: ProjectActivity, projectStartDate: string | null): { left: string; width: string } | null {
  const aStart = parseLocalDate(activity.start_date)
  const aEnd = parseLocalDate(activity.end_date)
  if (!aStart || !aEnd || !projectStartDate) return null
  const yearStart = new Date(selectedYear.value, 0, 1)
  const yearEnd = new Date(selectedYear.value, 11, 31)
  if (aEnd < yearStart || aStart > yearEnd) return null
  const effStart = aStart < yearStart ? yearStart : aStart
  const effEnd = aEnd > yearEnd ? yearEnd : aEnd
  const left = (effStart.getMonth() / 12) * 100
  const width = Math.max(((effEnd.getMonth() - effStart.getMonth() + 1) / 12) * 100, 2)
  return { left: `${left}%`, width: `${width}%` }
}

// ── Activity status colors ────────────────────────────────────────────────────
const activityBarColor: Record<string, string> = {
  pending:     '#94a3b8',
  in_progress: '#3b82f6',
  done:        '#22c55e',
  blocked:     '#ef4444',
}

// ── Expand / collapse ─────────────────────────────────────────────────────────
async function toggleProject(projectId: number) {
  if (expandedProjects.value.has(projectId)) {
    expandedProjects.value = new Set([...expandedProjects.value].filter(id => id !== projectId))
    return
  }
  expandedProjects.value = new Set([...expandedProjects.value, projectId])
  if (activitiesMap.value[projectId]) return
  loadingActivities.value = new Set([...loadingActivities.value, projectId])
  try {
    const acts = await projectActivitiesApi.list(projectId)
    activitiesMap.value = { ...activitiesMap.value, [projectId]: acts }
  } catch {
    // ignore
  } finally {
    loadingActivities.value = new Set([...loadingActivities.value].filter(id => id !== projectId))
  }
}
</script>

<template>
  <div class="flex flex-col h-full bg-gray-50">
    <!-- Header -->
    <div class="bg-white border-b border-gray-200 px-6 py-3">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-base font-bold text-gray-900">Vista Global de Proyectos</h2>
          <p class="text-xs text-gray-500 mt-0.5">
            {{ projects.length }} proyectos · {{ totalActivities }} actividades cargadas
          </p>
        </div>
        <!-- Year navigation -->
        <div class="flex items-center gap-1">
          <button
            v-for="y in availableYears"
            :key="y"
            class="px-3 py-1 rounded text-sm font-medium transition-colors"
            :class="y === selectedYear
              ? 'bg-blue-600 text-white'
              : 'text-gray-500 hover:bg-gray-100'"
            @click="selectedYear = y"
          >
            {{ y }}
          </button>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="mx-6 mt-3 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-2 text-sm">
      {{ error }}
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <div v-else class="flex-1 overflow-auto">
      <!-- Column header -->
      <div class="flex sticky top-0 z-10 bg-white border-b border-gray-200 shadow-sm">
        <div class="w-64 flex-shrink-0 px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">
          Proyecto
        </div>
        <div class="flex-1 flex">
          <div
            v-for="(month, idx) in monthNames"
            :key="idx"
            class="flex-1 text-center text-xs text-gray-400 font-medium py-2 border-l border-gray-100"
          >
            {{ month }}
          </div>
        </div>
      </div>

      <!-- WP groups -->
      <div v-for="(groupProjects, wp) in groupedProjects" :key="wp" class="border-b border-gray-100">
        <!-- WP header -->
        <div
          class="flex items-center gap-2 px-3 py-1.5 bg-gray-50"
        >
          <div
            class="w-2.5 h-2.5 rounded-full flex-shrink-0"
            :style="{ backgroundColor: getWpColor(wp as string) }"
          />
          <span class="text-xs font-bold text-gray-600 uppercase tracking-wide">{{ wp }}</span>
          <span class="text-xs text-gray-400">({{ groupProjects.length }})</span>
        </div>

        <!-- Project rows -->
        <div v-for="project in groupProjects" :key="project.id">
          <!-- Project row -->
          <div class="flex items-center hover:bg-blue-50/30 group">
            <!-- Left: project info -->
            <div class="w-64 flex-shrink-0 flex items-center gap-1.5 px-3 py-2">
              <button
                class="p-0.5 text-gray-400 hover:text-gray-600 flex-shrink-0"
                @click="toggleProject(project.id)"
              >
                <component
                  :is="expandedProjects.has(project.id) ? ChevronDown : ChevronRight"
                  class="w-3.5 h-3.5"
                />
              </button>
              <div
                class="w-2 h-2 rounded-full flex-shrink-0"
                :style="{ backgroundColor: project.color ?? getWpColor(project.work_package) }"
              />
              <span class="text-xs text-gray-700 truncate leading-tight" :title="project.title">
                {{ project.title }}
              </span>
            </div>

            <!-- Right: timeline bar -->
            <div class="flex-1 relative h-8 flex">
              <!-- Month grid lines -->
              <div
                v-for="(_, idx) in monthNames"
                :key="idx"
                class="flex-1 h-full border-l border-gray-100"
              />
              <!-- Project bar -->
              <div
                v-if="getProjectBar(project)"
                class="absolute top-1.5 bottom-1.5 rounded cursor-default opacity-80 group-hover:opacity-100 transition-opacity"
                :style="{
                  left: getProjectBar(project)!.left,
                  width: getProjectBar(project)!.width,
                  backgroundColor: project.color ?? getWpColor(project.work_package),
                }"
                :title="`${project.title}: ${project.start_date} → ${project.end_date}`"
              />
            </div>
          </div>

          <!-- Activity rows (when expanded) -->
          <template v-if="expandedProjects.has(project.id)">
            <div v-if="loadingActivities.has(project.id)" class="flex items-center justify-center py-2">
              <div class="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
            </div>
            <div
              v-else-if="activitiesMap[project.id]?.length === 0"
              class="pl-16 py-1 text-xs text-gray-400"
            >
              Sin actividades
            </div>
            <div
              v-for="act in activitiesMap[project.id]"
              v-else
              :key="act.id"
              class="flex items-center bg-gray-50/60"
            >
              <!-- Left: activity info -->
              <div class="w-64 flex-shrink-0 flex items-center gap-1.5 px-3 py-1 pl-10">
                <span class="text-xs text-gray-400 font-mono">
                  {{ act.number != null ? `#${act.number}` : '·' }}
                </span>
                <span class="text-xs text-gray-600 truncate" :title="act.description">
                  {{ act.description }}
                </span>
              </div>
              <!-- Right: activity bar -->
              <div class="flex-1 relative h-6 flex">
                <div
                  v-for="(_, idx) in monthNames"
                  :key="idx"
                  class="flex-1 h-full border-l border-gray-100"
                />
                <div
                  v-if="getActivityBar(act, project.start_date)"
                  class="absolute top-1 bottom-1 rounded opacity-80"
                  :style="{
                    left: getActivityBar(act, project.start_date)!.left,
                    width: getActivityBar(act, project.start_date)!.width,
                    backgroundColor: activityBarColor[act.status] ?? '#94a3b8',
                  }"
                  :title="`${act.description} (${act.status})`"
                />
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- Legend -->
      <div class="flex items-center gap-4 px-4 py-3 flex-wrap">
        <span class="text-xs text-gray-400 font-medium">Actividades:</span>
        <div class="flex items-center gap-1.5">
          <div class="w-3 h-3 rounded" style="background-color: #94a3b8" />
          <span class="text-xs text-gray-500">Pendiente</span>
        </div>
        <div class="flex items-center gap-1.5">
          <div class="w-3 h-3 rounded" style="background-color: #3b82f6" />
          <span class="text-xs text-gray-500">En curso</span>
        </div>
        <div class="flex items-center gap-1.5">
          <div class="w-3 h-3 rounded" style="background-color: #22c55e" />
          <span class="text-xs text-gray-500">Terminada</span>
        </div>
        <div class="flex items-center gap-1.5">
          <div class="w-3 h-3 rounded" style="background-color: #ef4444" />
          <span class="text-xs text-gray-500">Bloqueada</span>
        </div>
      </div>
    </div>
  </div>
</template>
