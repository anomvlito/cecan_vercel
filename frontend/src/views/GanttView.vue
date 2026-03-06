<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import Gantt from 'frappe-gantt'
import { projectsApi, projectActivitiesApi, responsibilitiesApi } from '@/services/api'
import type { ScientificProject, ProjectActivity, ResponsibilityAssignment } from '@/types/publication'
import {
  Plus, Trash2, ChevronDown, ChevronUp, X, Users, Save, AlertCircle,
} from 'lucide-vue-next'

// ── State ────────────────────────────────────────────────────────────────────
const projects = ref<ScientificProject[]>([])
const selectedProjectId = ref<number | null>(null)
const activities = ref<ProjectActivity[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const ganttContainer = ref<HTMLElement | null>(null)
let ganttInstance: InstanceType<typeof Gantt> | null = null

const viewMode = ref<'Month' | 'Week' | 'Quarter Day' | 'Half Day' | 'Day'>('Month')

// Panel de edición/creación
const showPanel = ref(false)
const editingActivity = ref<ProjectActivity | null>(null)
const form = ref({
  description: '',
  number: null as number | null,
  start_month: 1,
  end_month: 1,
  status: 'pending',
  progress: 0,
  budget_allocated: null as number | null,
  notes: null as string | null,
  sort_order: 0,
})
const saving = ref(false)

// Panel RACI
const showRaciPanel = ref(false)
const raciActivityId = ref<number | null>(null)
const raciActivityDesc = ref('')
const responsibilities = ref<ResponsibilityAssignment[]>([])
const raciForm = ref({ member_id: null as number | null, raci_role: 'R' })
const savingRaci = ref(false)

// ── Proyectos ────────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    const res = await projectsApi.search({ limit: 200 })
    projects.value = res.items
  } catch {
    error.value = 'Error al cargar proyectos'
  }
})

// ── Actividades ──────────────────────────────────────────────────────────────
async function loadActivities() {
  if (!selectedProjectId.value) return
  loading.value = true
  error.value = null
  try {
    activities.value = await projectActivitiesApi.list(selectedProjectId.value)
    await nextTick()
    renderGantt()
  } catch {
    error.value = 'Error al cargar actividades'
  } finally {
    loading.value = false
  }
}

watch(selectedProjectId, loadActivities)

// ── Gantt ────────────────────────────────────────────────────────────────────
const ganttTasks = computed(() => {
  return activities.value
    .filter(a => a.start_date && a.end_date)
    .map(a => ({
      id: String(a.id),
      name: `${a.number ? '#' + a.number + ' ' : ''}${a.description}`,
      start: a.start_date!,
      end: a.end_date!,
      progress: a.progress,
      custom_class: statusClass(a.status),
    }))
})

function statusClass(s: string) {
  if (s === 'done') return 'gantt-done'
  if (s === 'in_progress') return 'gantt-inprogress'
  if (s === 'blocked') return 'gantt-blocked'
  return 'gantt-pending'
}

function renderGantt() {
  if (!ganttContainer.value || ganttTasks.value.length === 0) return
  if (ganttInstance) {
    ganttInstance.refresh(ganttTasks.value)
    ganttInstance.change_view_mode(viewMode.value)
    return
  }
  ganttInstance = new Gantt(ganttContainer.value, ganttTasks.value, {
    view_mode: viewMode.value,
    date_format: 'YYYY-MM-DD',
    on_click: (task: { id: string }) => {
      const act = activities.value.find(a => String(a.id) === task.id)
      if (act) openEdit(act)
    },
    on_progress_change: async (task: { id: string }, progress: number) => {
      const id = parseInt(task.id)
      await projectActivitiesApi.update(id, { progress })
      const idx = activities.value.findIndex(a => a.id === id)
      if (idx >= 0) activities.value[idx] = { ...activities.value[idx]!, progress }
    },
  })
}

watch(viewMode, () => {
  if (ganttInstance) {
    ganttInstance.change_view_mode(viewMode.value)
  }
})

watch(ganttTasks, async () => {
  await nextTick()
  renderGantt()
})

// ── Panel edición ─────────────────────────────────────────────────────────────
function openCreate() {
  editingActivity.value = null
  form.value = {
    description: '',
    number: null,
    start_month: 1,
    end_month: 1,
    status: 'pending',
    progress: 0,
    budget_allocated: null,
    notes: null,
    sort_order: activities.value.length,
  }
  showPanel.value = true
}

function openEdit(act: ProjectActivity) {
  editingActivity.value = act
  form.value = {
    description: act.description,
    number: act.number,
    start_month: act.start_month,
    end_month: act.end_month,
    status: act.status,
    progress: act.progress,
    budget_allocated: act.budget_allocated,
    notes: act.notes,
    sort_order: act.sort_order,
  }
  showPanel.value = true
}

async function saveActivity() {
  if (!selectedProjectId.value || !form.value.description.trim()) return
  saving.value = true
  try {
    if (editingActivity.value) {
      const updated = await projectActivitiesApi.update(editingActivity.value.id, form.value)
      const idx = activities.value.findIndex(a => a.id === editingActivity.value!.id)
      if (idx >= 0) activities.value[idx] = updated
    } else {
      const created = await projectActivitiesApi.create({
        project_id: selectedProjectId.value,
        ...form.value,
      })
      activities.value.push(created)
    }
    showPanel.value = false
  } catch {
    error.value = 'Error al guardar actividad'
  } finally {
    saving.value = false
  }
}

async function deleteActivity(id: number) {
  if (!confirm('¿Eliminar esta actividad?')) return
  try {
    await projectActivitiesApi.delete(id)
    activities.value = activities.value.filter(a => a.id !== id)
  } catch {
    error.value = 'Error al eliminar'
  }
}

// ── Panel RACI ────────────────────────────────────────────────────────────────
async function openRaci(act: ProjectActivity) {
  raciActivityId.value = act.id
  raciActivityDesc.value = act.description
  responsibilities.value = await responsibilitiesApi.list('activity', act.id)
  raciForm.value = { member_id: null, raci_role: 'R' }
  showRaciPanel.value = true
}

async function addRaci() {
  if (!raciActivityId.value || !raciForm.value.member_id) return
  savingRaci.value = true
  try {
    const created = await responsibilitiesApi.create({
      resource_type: 'activity',
      resource_id: raciActivityId.value,
      raci_role: raciForm.value.raci_role,
      member_id: raciForm.value.member_id,
    })
    responsibilities.value.push(created)
  } catch {
    error.value = 'Error al asignar responsable'
  } finally {
    savingRaci.value = false
  }
}

async function removeRaci(id: number) {
  await responsibilitiesApi.delete(id)
  responsibilities.value = responsibilities.value.filter(r => r.id !== id)
}

// ── Helpers ───────────────────────────────────────────────────────────────────
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
  R: 'bg-blue-100 text-blue-700',
  A: 'bg-yellow-100 text-yellow-700',
  C: 'bg-purple-100 text-purple-700',
  I: 'bg-gray-100 text-gray-600',
}
const raciLabels: Record<string, string> = {
  R: 'Responsible',
  A: 'Accountable',
  C: 'Consulted',
  I: 'Informed',
}

const selectedProject = computed(() =>
  projects.value.find(p => p.id === selectedProjectId.value) ?? null,
)
</script>

<template>
  <div class="flex flex-col h-full bg-gray-50">
    <!-- Header -->
    <div class="bg-white border-b border-gray-200 px-6 py-4 flex items-center gap-4">
      <div>
        <h1 class="text-xl font-bold text-gray-900">Planificación Gantt</h1>
        <p class="text-sm text-gray-500">Actividades y cronograma de proyectos</p>
      </div>
      <div class="ml-auto flex items-center gap-3">
        <!-- Selector de proyecto -->
        <select
          v-model="selectedProjectId"
          class="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 min-w-64"
        >
          <option :value="null">Seleccionar proyecto…</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">
            {{ p.title }}
          </option>
        </select>
        <!-- View mode -->
        <select
          v-model="viewMode"
          class="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="Month">Mes</option>
          <option value="Week">Semana</option>
          <option value="Day">Día</option>
        </select>
        <button
          v-if="selectedProjectId"
          class="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          @click="openCreate"
        >
          <Plus class="w-4 h-4" />
          Nueva actividad
        </button>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="mx-6 mt-4 flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
      <AlertCircle class="w-4 h-4 flex-shrink-0" />
      {{ error }}
      <button class="ml-auto text-red-400 hover:text-red-600" @click="error = null"><X class="w-4 h-4" /></button>
    </div>

    <!-- Empty state -->
    <div v-if="!selectedProjectId" class="flex-1 flex items-center justify-center">
      <div class="text-center text-gray-400">
        <svg class="w-16 h-16 mx-auto mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
        </svg>
        <p class="text-lg font-medium">Selecciona un proyecto para ver su Gantt</p>
      </div>
    </div>

    <div v-else class="flex flex-1 min-h-0 gap-0">
      <!-- Lista de actividades -->
      <div class="w-80 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col">
        <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
          <span class="text-sm font-semibold text-gray-700">Actividades ({{ activities.length }})</span>
          <span v-if="selectedProject?.start_date" class="text-xs text-gray-400">
            Inicio: {{ new Date(selectedProject.start_date).toLocaleDateString('es-CL') }}
          </span>
        </div>

        <div v-if="loading" class="flex-1 flex items-center justify-center">
          <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>

        <div v-else-if="activities.length === 0" class="flex-1 flex items-center justify-center text-gray-400 text-sm p-4 text-center">
          Sin actividades. Crea la primera con el botón de arriba.
        </div>

        <div v-else class="flex-1 overflow-y-auto divide-y divide-gray-50">
          <div
            v-for="act in activities"
            :key="act.id"
            class="px-4 py-3 hover:bg-gray-50 group"
          >
            <div class="flex items-start gap-2">
              <span class="text-xs font-mono text-gray-400 mt-0.5 flex-shrink-0">
                {{ act.number != null ? '#' + act.number : '—' }}
              </span>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-800 line-clamp-2 leading-tight">{{ act.description }}</p>
                <div class="flex items-center gap-2 mt-1 flex-wrap">
                  <span class="text-xs rounded-full px-2 py-0.5 font-medium" :class="statusBadge[act.status] ?? 'bg-gray-100 text-gray-600'">
                    {{ statusLabel[act.status] ?? act.status }}
                  </span>
                  <span class="text-xs text-gray-400">M{{ act.start_month }}–M{{ act.end_month }}</span>
                  <span class="text-xs text-gray-400">{{ act.progress }}%</span>
                </div>
              </div>
              <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                <button class="p-1 text-gray-400 hover:text-purple-600 rounded" title="RACI" @click="openRaci(act)">
                  <Users class="w-3.5 h-3.5" />
                </button>
                <button class="p-1 text-gray-400 hover:text-blue-600 rounded" title="Editar" @click="openEdit(act)">
                  <ChevronDown class="w-3.5 h-3.5" />
                </button>
                <button class="p-1 text-gray-400 hover:text-red-600 rounded" title="Eliminar" @click="deleteActivity(act.id)">
                  <Trash2 class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Gantt -->
      <div class="flex-1 flex flex-col min-w-0 bg-white">
        <div v-if="loading" class="flex-1 flex items-center justify-center">
          <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
        <div v-else-if="ganttTasks.length === 0 && activities.length > 0" class="flex-1 flex items-center justify-center text-gray-400 text-sm">
          Las actividades no tienen fechas calculadas. Asegúrate de que el proyecto tenga una fecha de inicio.
        </div>
        <div v-else class="flex-1 overflow-auto p-2">
          <div ref="ganttContainer" class="gantt-wrapper" />
        </div>
      </div>
    </div>

    <!-- ── Panel Edición/Creación ─────────────────────────────────────────── -->
    <Teleport to="body">
      <div v-if="showPanel" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" @click.self="showPanel = false">
        <div class="bg-white rounded-xl shadow-2xl w-full max-w-lg">
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <h2 class="text-lg font-semibold text-gray-900">
              {{ editingActivity ? 'Editar actividad' : 'Nueva actividad' }}
            </h2>
            <button class="text-gray-400 hover:text-gray-600" @click="showPanel = false">
              <X class="w-5 h-5" />
            </button>
          </div>
          <div class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Descripción *</label>
              <input
                v-model="form.description"
                type="text"
                placeholder="Descripción de la actividad"
                class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Número</label>
                <input
                  v-model.number="form.number"
                  type="number"
                  min="1"
                  placeholder="Ej. 1"
                  class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Estado</label>
                <select
                  v-model="form.status"
                  class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="pending">Pendiente</option>
                  <option value="in_progress">En curso</option>
                  <option value="done">Terminada</option>
                  <option value="blocked">Bloqueada</option>
                </select>
              </div>
            </div>
            <div class="grid grid-cols-3 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Mes inicio</label>
                <input
                  v-model.number="form.start_month"
                  type="number" min="1" max="60"
                  class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Mes fin</label>
                <input
                  v-model.number="form.end_month"
                  type="number" min="1" max="60"
                  class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Avance %</label>
                <input
                  v-model.number="form.progress"
                  type="number" min="0" max="100"
                  class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Presupuesto (CLP)</label>
                <input
                  v-model.number="form.budget_allocated"
                  type="number" min="0" step="1000"
                  placeholder="Opcional"
                  class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Orden</label>
                <input
                  v-model.number="form.sort_order"
                  type="number" min="0"
                  class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Notas</label>
              <textarea
                v-model="form.notes"
                rows="2"
                placeholder="Notas opcionales…"
                class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
            </div>
          </div>
          <div class="flex justify-end gap-3 px-6 py-4 border-t border-gray-200">
            <button class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800" @click="showPanel = false">Cancelar</button>
            <button
              class="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
              :disabled="saving || !form.description.trim()"
              @click="saveActivity"
            >
              <Save class="w-4 h-4" />
              {{ saving ? 'Guardando…' : 'Guardar' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ── Panel RACI ─────────────────────────────────────────────────────── -->
    <Teleport to="body">
      <div v-if="showRaciPanel" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" @click.self="showRaciPanel = false">
        <div class="bg-white rounded-xl shadow-2xl w-full max-w-md">
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <div>
              <h2 class="text-lg font-semibold text-gray-900">Responsables RACI</h2>
              <p class="text-xs text-gray-500 mt-0.5 line-clamp-1">{{ raciActivityDesc }}</p>
            </div>
            <button class="text-gray-400 hover:text-gray-600" @click="showRaciPanel = false">
              <X class="w-5 h-5" />
            </button>
          </div>
          <div class="p-6 space-y-4">
            <!-- Lista actual -->
            <div v-if="responsibilities.length === 0" class="text-sm text-gray-400 text-center py-2">
              Sin asignaciones aún
            </div>
            <div v-else class="space-y-2">
              <div
                v-for="r in responsibilities"
                :key="r.id"
                class="flex items-center gap-3 rounded-lg border border-gray-100 px-3 py-2"
              >
                <span class="text-xs font-bold rounded px-1.5 py-0.5" :class="raciColors[r.raci_role]">
                  {{ r.raci_role }}
                </span>
                <span class="flex-1 text-sm text-gray-700">{{ r.member_name ?? 'Sin nombre' }}</span>
                <span class="text-xs text-gray-400">{{ raciLabels[r.raci_role] }}</span>
                <button class="text-gray-300 hover:text-red-500" @click="removeRaci(r.id)">
                  <X class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <!-- Agregar -->
            <div class="border-t border-gray-100 pt-4 space-y-3">
              <p class="text-sm font-medium text-gray-700">Agregar responsable</p>
              <div class="flex gap-2">
                <input
                  v-model.number="raciForm.member_id"
                  type="number"
                  placeholder="ID del miembro"
                  class="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <select
                  v-model="raciForm.raci_role"
                  class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="R">R — Responsible</option>
                  <option value="A">A — Accountable</option>
                  <option value="C">C — Consulted</option>
                  <option value="I">I — Informed</option>
                </select>
                <button
                  class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                  :disabled="savingRaci || !raciForm.member_id"
                  @click="addRaci"
                >
                  <Plus class="w-4 h-4" />
                </button>
              </div>
              <p class="text-xs text-gray-400">Puedes obtener el ID del miembro desde la sección Investigadores.</p>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
/* Contenedor del gantt */
.gantt-wrapper :deep(.gantt-container) {
  border: none;
}
.gantt-wrapper :deep(.bar-wrapper .bar) {
  fill: #3b82f6;
}
.gantt-wrapper :deep(.bar-wrapper.gantt-done .bar) {
  fill: #22c55e;
}
.gantt-wrapper :deep(.bar-wrapper.gantt-inprogress .bar) {
  fill: #f59e0b;
}
.gantt-wrapper :deep(.bar-wrapper.gantt-blocked .bar) {
  fill: #ef4444;
}
.gantt-wrapper :deep(.bar-wrapper.gantt-pending .bar) {
  fill: #6b7280;
}
</style>
