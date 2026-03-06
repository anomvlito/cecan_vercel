<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { projectsApi, projectActivitiesApi, responsibilitiesApi } from '@/services/api'
import type { ScientificProject, ProjectActivity, ResponsibilityAssignment } from '@/types/publication'
import MiniGantt from '@/components/projects/MiniGantt.vue'
import ActivityStatusModal from '@/components/projects/ActivityStatusModal.vue'
import ProjectsGantt from '@/components/projects/ProjectsGantt.vue'
import {
  Plus, Trash2, Users, X, AlertCircle, Save, BarChart2, List,
} from 'lucide-vue-next'

// ── Tabs ──────────────────────────────────────────────────────────────────────
const activeTab = ref<'project' | 'global'>('project')

// ── State ─────────────────────────────────────────────────────────────────────
const projects = ref<ScientificProject[]>([])
const selectedProjectId = ref<number | null>(null)
const activities = ref<ProjectActivity[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

// ── ActivityStatusModal ───────────────────────────────────────────────────────
const statusModalActivity = ref<ProjectActivity | null>(null)

function openStatusModal(act: ProjectActivity) {
  statusModalActivity.value = act
}

function closeStatusModal() {
  statusModalActivity.value = null
}

async function saveStatus(
  status: string,
  progress: number,
  budget: number | null,
  paymentStatus: string,
) {
  const act = statusModalActivity.value
  if (!act) return
  try {
    await projectActivitiesApi.update(act.id, {
      status,
      progress,
      budget_allocated: budget,
      payment_status: paymentStatus,
    })
    await loadActivities()
  } catch {
    error.value = 'Error al guardar estado'
  } finally {
    statusModalActivity.value = null
  }
}

// ── Projects ──────────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    const res = await projectsApi.search({ limit: 200 })
    projects.value = res.items
  } catch {
    error.value = 'Error al cargar proyectos'
  }
})

// ── Activities ────────────────────────────────────────────────────────────────
async function loadActivities() {
  if (!selectedProjectId.value) {
    activities.value = []
    return
  }
  loading.value = true
  error.value = null
  try {
    activities.value = await projectActivitiesApi.list(selectedProjectId.value)
  } catch {
    error.value = 'Error al cargar actividades'
  } finally {
    loading.value = false
  }
}

watch(selectedProjectId, loadActivities)

// ── Parsea fecha ISO (YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS) como hora local ───────
function parseLocalDate(str: string | null | undefined): Date | null {
  if (!str) return null
  const d = new Date(str.split('T')[0] + 'T00:00:00')
  return isNaN(d.getTime()) ? null : d
}

// ── Total months (desde fechas del proyecto si están disponibles) ─────────────
const totalMonths = computed(() => {
  const proj = selectedProject.value
  const s = parseLocalDate(proj?.start_date)
  const e = parseLocalDate(proj?.end_date)
  if (s && e) {
    const months = (e.getFullYear() - s.getFullYear()) * 12 + e.getMonth() - s.getMonth() + 1
    if (months > 0) return months
  }
  if (!activities.value.length) return 12
  return Math.max(...activities.value.map(a => a.end_month || 1), 12)
})

// ── Opciones de mes para el formulario (basadas en fecha inicio del proyecto) ─
const monthOptions = computed(() => {
  const start = parseLocalDate(selectedProject.value?.start_date)
  if (!start) {
    return Array.from({ length: 60 }, (_, i) => ({ value: i + 1, label: `Mes ${i + 1}` }))
  }
  return Array.from({ length: totalMonths.value }, (_, i) => {
    const d = new Date(start.getFullYear(), start.getMonth() + i)
    const label = d.toLocaleDateString('es-CL', { month: 'short', year: 'numeric' })
    return { value: i + 1, label: label.charAt(0).toUpperCase() + label.slice(1) }
  })
})

// ── Función para mostrar rango de fechas real de una actividad ────────────────
function activityDateRange(act: ProjectActivity): string {
  const s = parseLocalDate(act.start_date)
  const e = parseLocalDate(act.end_date)
  if (s && e) {
    const fmt = (d: Date) => d.toLocaleDateString('es-CL', { day: 'numeric', month: 'short', year: '2-digit' })
    return `${fmt(s)} → ${fmt(e)}`
  }
  return `M${act.start_month} → M${act.end_month}`
}

// ── Add activity form ─────────────────────────────────────────────────────────
const addForm = ref({
  description: '',
  start_month: 1,
  end_month: 1,
})
const saving = ref(false)

async function createActivity() {
  if (!selectedProjectId.value || !addForm.value.description.trim()) return
  saving.value = true
  try {
    await projectActivitiesApi.create({
      project_id: selectedProjectId.value,
      description: addForm.value.description,
      start_month: addForm.value.start_month,
      end_month: addForm.value.end_month,
      sort_order: activities.value.length,
    })
    addForm.value = { description: '', start_month: 1, end_month: addForm.value.start_month }
    await loadActivities()
  } catch {
    error.value = 'Error al crear actividad'
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

// ── RACI panel ────────────────────────────────────────────────────────────────
const showRaciPanel = ref(false)
const raciActivityId = ref<number | null>(null)
const raciActivityDesc = ref('')
const responsibilities = ref<ResponsibilityAssignment[]>([])
const raciForm = ref({ member_id: null as number | null, raci_role: 'R' })
const savingRaci = ref(false)

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
    responsibilities.value = [...responsibilities.value, created]
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
  pending:     'Pendiente',
  in_progress: 'En curso',
  done:        'Terminada',
  blocked:     'Bloqueada',
}

const statusBadge: Record<string, string> = {
  pending:     'bg-gray-100 text-gray-600',
  in_progress: 'bg-blue-100 text-blue-700',
  done:        'bg-green-100 text-green-700',
  blocked:     'bg-red-100 text-red-700',
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
    <div class="bg-white border-b border-gray-200 px-6 py-3 space-y-2">
      <div class="flex items-center justify-between">
        <h1 class="text-lg font-bold text-gray-900">Planificación Gantt</h1>
        <!-- Tab buttons -->
        <div class="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
          <button
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
            :class="activeTab === 'project'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-500 hover:text-gray-700'"
            @click="activeTab = 'project'"
          >
            <List class="w-4 h-4" />
            Por Proyecto
          </button>
          <button
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
            :class="activeTab === 'global'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-500 hover:text-gray-700'"
            @click="activeTab = 'global'"
          >
            <BarChart2 class="w-4 h-4" />
            Vista Global
          </button>
        </div>
      </div>

      <!-- Project selector (only in project tab) -->
      <div v-if="activeTab === 'project'" class="flex items-center gap-2">
        <select
          v-model="selectedProjectId"
          class="flex-1 min-w-0 border border-gray-300 rounded-lg px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option :value="null">Seleccionar proyecto…</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">
            {{ p.title }}
          </option>
        </select>
      </div>
    </div>

    <!-- Error bar -->
    <div
      v-if="error"
      class="mx-6 mt-4 flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm"
    >
      <AlertCircle class="w-4 h-4 flex-shrink-0" />
      {{ error }}
      <button class="ml-auto text-red-400 hover:text-red-600" @click="error = null">
        <X class="w-4 h-4" />
      </button>
    </div>

    <!-- ── GLOBAL TAB ──────────────────────────────────────────────────────── -->
    <div v-if="activeTab === 'global'" class="flex-1 min-h-0 overflow-hidden">
      <ProjectsGantt />
    </div>

    <!-- ── PROJECT TAB ────────────────────────────────────────────────────── -->
    <template v-else>
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
        <!-- LEFT: activity list (w-80) -->
        <div class="w-80 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col">
          <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
            <span class="text-sm font-semibold text-gray-700">
              Actividades ({{ activities.length }})
            </span>
            <span v-if="selectedProject?.start_date" class="text-xs text-gray-400">
              Inicio: {{ parseLocalDate(selectedProject.start_date)?.toLocaleDateString('es-CL') ?? '—' }}
            </span>
          </div>

          <div v-if="loading" class="flex-1 flex items-center justify-center">
            <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>

          <div
            v-else-if="activities.length === 0"
            class="flex-1 flex items-center justify-center text-gray-400 text-sm p-4 text-center"
          >
            Sin actividades. Crea la primera en el panel derecho.
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
                  <p class="text-sm font-medium text-gray-800 line-clamp-2 leading-tight">
                    {{ act.description }}
                  </p>
                  <div class="flex items-center gap-2 mt-1 flex-wrap">
                    <span
                      class="text-xs rounded-full px-2 py-0.5 font-medium"
                      :class="statusBadge[act.status] ?? 'bg-gray-100 text-gray-600'"
                    >
                      {{ statusLabel[act.status] ?? act.status }}
                    </span>
                    <span class="text-xs text-gray-400">{{ activityDateRange(act) }}</span>
                    <span class="text-xs text-gray-400">{{ act.progress }}%</span>
                  </div>
                </div>
                <!-- Hover action buttons -->
                <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                  <button
                    class="p-1 text-gray-400 hover:text-blue-600 rounded"
                    title="Actualizar estado"
                    @click="openStatusModal(act)"
                  >
                    <Save class="w-3.5 h-3.5" />
                  </button>
                  <button
                    class="p-1 text-gray-400 hover:text-purple-600 rounded"
                    title="RACI"
                    @click="openRaci(act)"
                  >
                    <Users class="w-3.5 h-3.5" />
                  </button>
                  <button
                    class="p-1 text-gray-400 hover:text-red-600 rounded"
                    title="Eliminar"
                    @click="deleteActivity(act.id)"
                  >
                    <Trash2 class="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- RIGHT: MiniGantt + add form -->
        <div class="flex-1 flex flex-col min-w-0 bg-white overflow-hidden">
          <div v-if="loading" class="flex-1 flex items-center justify-center">
            <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>

          <div v-else class="flex-1 overflow-auto p-4 flex flex-col gap-4">
            <!-- MiniGantt -->
            <div class="min-w-0">
              <MiniGantt
                :activities="activities"
                :total-months="totalMonths"
                :project-start-date="selectedProject?.start_date"
                @activity-click="openStatusModal"
              />
            </div>

            <!-- Add activity form -->
            <div class="bg-gray-50 rounded-xl border border-gray-200 p-4">
              <p class="text-sm font-semibold text-gray-700 mb-3">Nueva actividad</p>
              <div class="flex flex-col gap-3">
                <input
                  v-model="addForm.description"
                  type="text"
                  placeholder="Descripción de la actividad *"
                  class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  @keyup.enter="createActivity"
                />
                <div class="flex items-center gap-3 flex-wrap">
                  <div class="flex items-center gap-2 flex-1 min-w-0">
                    <label class="text-xs text-gray-500 whitespace-nowrap">Inicio</label>
                    <select
                      v-model.number="addForm.start_month"
                      class="flex-1 min-w-0 border border-gray-300 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                    >
                      <option v-for="opt in monthOptions" :key="opt.value" :value="opt.value">
                        {{ opt.label }}
                      </option>
                    </select>
                  </div>
                  <div class="flex items-center gap-2 flex-1 min-w-0">
                    <label class="text-xs text-gray-500 whitespace-nowrap">Fin</label>
                    <select
                      v-model.number="addForm.end_month"
                      class="flex-1 min-w-0 border border-gray-300 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                    >
                      <option
                        v-for="opt in monthOptions.filter(o => o.value >= addForm.start_month)"
                        :key="opt.value"
                        :value="opt.value"
                      >
                        {{ opt.label }}
                      </option>
                    </select>
                  </div>
                  <button
                    class="flex items-center gap-1.5 bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    :disabled="saving || !addForm.description.trim()"
                    @click="createActivity"
                  >
                    <Plus class="w-4 h-4" />
                    {{ saving ? 'Guardando…' : 'Crear' }}
                  </button>
                </div>
                <p
                  v-if="!selectedProject?.start_date"
                  class="text-xs text-amber-600"
                >
                  ⚠ El proyecto no tiene fecha de inicio definida — los meses se muestran como M1, M2…
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- ── ActivityStatusModal ─────────────────────────────────────────────── -->
    <ActivityStatusModal
      :activity="statusModalActivity"
      @close="closeStatusModal"
      @save="saveStatus"
    />

    <!-- ── RACI Panel ──────────────────────────────────────────────────────── -->
    <Teleport to="body">
      <div
        v-if="showRaciPanel"
        class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4"
        @click.self="showRaciPanel = false"
      >
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
            <!-- Current list -->
            <div v-if="responsibilities.length === 0" class="text-sm text-gray-400 text-center py-2">
              Sin asignaciones aún
            </div>
            <div v-else class="space-y-2">
              <div
                v-for="r in responsibilities"
                :key="r.id"
                class="flex items-center gap-3 rounded-lg border border-gray-100 px-3 py-2"
              >
                <span
                  class="text-xs font-bold rounded px-1.5 py-0.5"
                  :class="raciColors[r.raci_role]"
                >
                  {{ r.raci_role }}
                </span>
                <span class="flex-1 text-sm text-gray-700">{{ r.member_name ?? 'Sin nombre' }}</span>
                <span class="text-xs text-gray-400">{{ raciLabels[r.raci_role] }}</span>
                <button class="text-gray-300 hover:text-red-500" @click="removeRaci(r.id)">
                  <X class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <!-- Add form -->
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
              <p class="text-xs text-gray-400">
                Puedes obtener el ID del miembro desde la sección Investigadores.
              </p>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
