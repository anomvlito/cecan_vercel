<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { responsibilitiesApi } from '@/services/api'
import type { MyTask, AcademicMember } from '@/types/publication'
import { AlertTriangle, CheckCircle2, Clock, ChevronRight, Filter, X } from 'lucide-vue-next'

// ── State ─────────────────────────────────────────────────────────────────────
const tasks = ref<MyTask[]>([])
const members = ref<AcademicMember[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const filterMemberId = ref<number | null>(null)
const filterRole = ref<string>('')
const filterStatus = ref<string>('')
const filterOverdue = ref<boolean | null>(null)

// ── Load ───────────────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    const [t, m] = await Promise.all([
      responsibilitiesApi.myTasks(),
      responsibilitiesApi.myTasksMembers(),
    ])
    tasks.value = t
    members.value = m
  } catch {
    error.value = 'Error al cargar tareas'
  } finally {
    loading.value = false
  }
})

async function applyMemberFilter() {
  loading.value = true
  try {
    tasks.value = await responsibilitiesApi.myTasks(filterMemberId.value ?? undefined)
  } catch {
    error.value = 'Error al filtrar'
  } finally {
    loading.value = false
  }
}

// ── Computed ───────────────────────────────────────────────────────────────────
const filtered = computed(() => {
  return tasks.value.filter(t => {
    if (filterRole.value && t.raci_role !== filterRole.value) return false
    if (filterStatus.value && t.status !== filterStatus.value) return false
    if (filterOverdue.value === true && !t.is_overdue) return false
    if (filterOverdue.value === false && t.is_overdue) return false
    return true
  })
})

const stats = computed(() => ({
  total: filtered.value.length,
  overdue: filtered.value.filter(t => t.is_overdue).length,
  done: filtered.value.filter(t => t.status === 'done').length,
  inProgress: filtered.value.filter(t => t.status === 'in_progress').length,
}))

// Agrupar por proyecto
const grouped = computed(() => {
  const map = new Map<string, { projectId: number; tasks: MyTask[] }>()
  for (const t of filtered.value) {
    if (!map.has(t.project_title)) {
      map.set(t.project_title, { projectId: t.project_id, tasks: [] })
    }
    map.get(t.project_title)!.tasks.push(t)
  }
  return Array.from(map.entries()).map(([title, v]) => ({ title, ...v }))
})

// ── Helpers ────────────────────────────────────────────────────────────────────
const statusLabel: Record<string, string> = {
  pending: 'Pendiente',
  in_progress: 'En curso',
  done: 'Terminada',
  blocked: 'Bloqueada',
}
const statusBadge: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-600',
  in_progress: 'bg-blue-100 text-blue-700',
  done: 'bg-green-100 text-green-700',
  blocked: 'bg-red-100 text-red-700',
}
const raciColors: Record<string, string> = {
  R: 'bg-blue-500',
  A: 'bg-yellow-500',
  C: 'bg-purple-500',
  I: 'bg-gray-400',
}
const raciLabels: Record<string, string> = {
  R: 'Responsible',
  A: 'Accountable',
  C: 'Consulted',
  I: 'Informed',
}

function formatDate(d: string | null) {
  if (!d) return '—'
  const date = new Date(d.split('T')[0] + 'T00:00:00')
  if (isNaN(date.getTime())) return '—'
  return date.toLocaleDateString('es-CL', { day: '2-digit', month: 'short', year: 'numeric' })
}
</script>

<template>
  <div class="flex flex-col h-full bg-gray-50">
    <!-- Header -->
    <div class="bg-white border-b border-gray-200 px-6 py-4">
      <h1 class="text-xl font-bold text-gray-900">Mis Tareas RACI</h1>
      <p class="text-sm text-gray-500">Actividades asignadas a investigadores por rol RACI</p>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-4 gap-4 px-6 py-4">
      <div class="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center">
          <Filter class="w-5 h-5 text-gray-500" />
        </div>
        <div>
          <p class="text-2xl font-bold text-gray-900">{{ stats.total }}</p>
          <p class="text-xs text-gray-500">Total tareas</p>
        </div>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center">
          <AlertTriangle class="w-5 h-5 text-red-500" />
        </div>
        <div>
          <p class="text-2xl font-bold text-red-600">{{ stats.overdue }}</p>
          <p class="text-xs text-gray-500">Vencidas</p>
        </div>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
          <Clock class="w-5 h-5 text-blue-500" />
        </div>
        <div>
          <p class="text-2xl font-bold text-blue-600">{{ stats.inProgress }}</p>
          <p class="text-xs text-gray-500">En curso</p>
        </div>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
          <CheckCircle2 class="w-5 h-5 text-green-500" />
        </div>
        <div>
          <p class="text-2xl font-bold text-green-600">{{ stats.done }}</p>
          <p class="text-xs text-gray-500">Terminadas</p>
        </div>
      </div>
    </div>

    <!-- Filtros -->
    <div class="bg-white border-y border-gray-200 px-6 py-3 flex items-center gap-3 flex-wrap">
      <span class="text-sm font-medium text-gray-500 mr-1">Filtros:</span>

      <!-- Miembro -->
      <select
        v-model="filterMemberId"
        class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        @change="applyMemberFilter"
      >
        <option :value="null">Todos los miembros</option>
        <option v-for="m in members" :key="m.id" :value="m.id">{{ m.full_name }}</option>
      </select>

      <!-- Rol RACI -->
      <select
        v-model="filterRole"
        class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">Todos los roles</option>
        <option value="R">R — Responsible</option>
        <option value="A">A — Accountable</option>
        <option value="C">C — Consulted</option>
        <option value="I">I — Informed</option>
      </select>

      <!-- Estado -->
      <select
        v-model="filterStatus"
        class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">Todos los estados</option>
        <option value="pending">Pendiente</option>
        <option value="in_progress">En curso</option>
        <option value="done">Terminada</option>
        <option value="blocked">Bloqueada</option>
      </select>

      <!-- Vencidas -->
      <select
        v-model="filterOverdue"
        class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option :value="null">Con y sin retraso</option>
        <option :value="true">Solo vencidas</option>
        <option :value="false">Solo vigentes</option>
      </select>

      <!-- Reset -->
      <button
        v-if="filterRole || filterStatus || filterOverdue !== null || filterMemberId"
        class="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 ml-auto"
        @click="filterRole = ''; filterStatus = ''; filterOverdue = null; filterMemberId = null; applyMemberFilter()"
      >
        <X class="w-3.5 h-3.5" />
        Limpiar filtros
      </button>
    </div>

    <!-- Error -->
    <div v-if="error" class="mx-6 mt-4 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
      {{ error }}
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Empty -->
    <div v-else-if="filtered.length === 0" class="flex-1 flex items-center justify-center text-gray-400">
      <div class="text-center">
        <CheckCircle2 class="w-12 h-12 mx-auto mb-3 opacity-30" />
        <p class="font-medium">No hay tareas para mostrar</p>
        <p class="text-sm mt-1">Ajusta los filtros o asigna responsables desde el Gantt</p>
      </div>
    </div>

    <!-- Tabla agrupada por proyecto -->
    <div v-else class="flex-1 overflow-auto px-6 py-4 space-y-6">
      <div
        v-for="group in grouped"
        :key="group.projectId"
        class="bg-white rounded-xl border border-gray-200 overflow-hidden"
      >
        <!-- Encabezado de proyecto -->
        <div class="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center gap-2">
          <ChevronRight class="w-4 h-4 text-gray-400" />
          <span class="font-semibold text-gray-800 text-sm">{{ group.title }}</span>
          <span class="ml-auto text-xs text-gray-400">{{ group.tasks.length }} actividades</span>
        </div>

        <!-- Actividades -->
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-100 text-xs text-gray-500">
              <th class="text-left px-4 py-2 font-medium">Actividad</th>
              <th class="text-left px-4 py-2 font-medium">Responsable</th>
              <th class="text-center px-4 py-2 font-medium">Rol</th>
              <th class="text-left px-4 py-2 font-medium">Estado</th>
              <th class="text-right px-4 py-2 font-medium">Avance</th>
              <th class="text-left px-4 py-2 font-medium">Vence</th>
              <th class="text-center px-4 py-2 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="task in group.tasks"
              :key="`${task.activity_id}-${task.raci_role}-${task.member_id}`"
              class="border-b border-gray-50 hover:bg-gray-50 transition-colors"
              :class="task.is_overdue ? 'bg-red-50/40' : ''"
            >
              <td class="px-4 py-3 text-gray-800 max-w-xs">
                <span class="line-clamp-2 leading-tight">{{ task.activity_description }}</span>
              </td>
              <td class="px-4 py-3 text-gray-600">{{ task.member_name ?? '—' }}</td>
              <td class="px-4 py-3 text-center">
                <span
                  class="inline-flex items-center gap-1 text-xs font-bold text-white rounded px-1.5 py-0.5"
                  :class="raciColors[task.raci_role]"
                  :title="raciLabels[task.raci_role]"
                >
                  {{ task.raci_role }}
                </span>
              </td>
              <td class="px-4 py-3">
                <span class="text-xs rounded-full px-2 py-0.5 font-medium" :class="statusBadge[task.status] ?? 'bg-gray-100 text-gray-600'">
                  {{ statusLabel[task.status] ?? task.status }}
                </span>
              </td>
              <td class="px-4 py-3 text-right">
                <div class="flex items-center justify-end gap-2">
                  <div class="w-20 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      class="h-full rounded-full transition-all"
                      :class="task.status === 'done' ? 'bg-green-500' : 'bg-blue-500'"
                      :style="{ width: task.progress + '%' }"
                    />
                  </div>
                  <span class="text-xs text-gray-500 w-8 text-right">{{ task.progress }}%</span>
                </div>
              </td>
              <td class="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">
                {{ formatDate(task.end_date) }}
              </td>
              <td class="px-4 py-3 text-center">
                <span v-if="task.is_overdue" title="Actividad vencida">
                  <AlertTriangle class="w-4 h-4 text-red-500" />
                </span>
                <span v-else-if="task.status === 'done'" title="Completada">
                  <CheckCircle2 class="w-4 h-4 text-green-500" />
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
