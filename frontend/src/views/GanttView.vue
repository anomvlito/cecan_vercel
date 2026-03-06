<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { projectsApi, projectActivitiesApi, responsibilitiesApi } from '@/services/api'
import type { ScientificProject, ProjectActivity, ResponsibilityAssignment } from '@/types/publication'
import DHMLXGantt from '@/components/projects/DHMLXGantt.vue'
import ActivityStatusModal from '@/components/projects/ActivityStatusModal.vue'
import ProjectsGantt from '@/components/projects/ProjectsGantt.vue'
import GuideLabel from '@/components/ui/GuideLabel.vue'
import AppTooltip from '@/components/ui/AppTooltip.vue'
import {
  Plus, Trash2, Users, X, AlertCircle, BarChart2, List, Calendar,
  ChevronsDownUp, ChevronsUpDown,
} from 'lucide-vue-next'

// ── Tabs ──────────────────────────────────────────────────────────────────────
const activeTab = ref<'project' | 'global'>('project')

// ── State ─────────────────────────────────────────────────────────────────────
const projects      = ref<ScientificProject[]>([])
const selectedProjectId = ref<number | null>(null)
const activities    = ref<ProjectActivity[]>([])
const loading       = ref(false)
const error         = ref<string | null>(null)
const ganttRef      = ref<InstanceType<typeof DHMLXGantt> | null>(null)
const globalGanttRef = ref<InstanceType<typeof ProjectsGantt> | null>(null)
const showAddForm   = ref(false)

// ── ActivityStatusModal ───────────────────────────────────────────────────────
const statusModalActivity = ref<ProjectActivity | null>(null)

function openStatusModal(actId: number) {
  const act = activities.value.find(a => a.id === actId)
  if (act) statusModalActivity.value = act
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
    await projectActivitiesApi.update(act.id, { status, progress, budget_allocated: budget, payment_status: paymentStatus })
    await loadActivities()
    ganttRef.value?.reload()
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
  if (!selectedProjectId.value) { activities.value = []; return }
  loading.value = true
  try {
    activities.value = await projectActivitiesApi.list(selectedProjectId.value)
  } catch {
    error.value = 'Error al cargar actividades'
  } finally {
    loading.value = false
  }
}

watch(selectedProjectId, loadActivities)

// ── Computed ──────────────────────────────────────────────────────────────────
const selectedProject = computed(() =>
  projects.value.find(p => p.id === selectedProjectId.value) ?? null,
)

function parseLocalDate(str: string | null | undefined): Date | null {
  if (!str) return null
  const d = new Date(str.split('T')[0] + 'T00:00:00')
  return isNaN(d.getTime()) ? null : d
}

function fmtDate(str: string | null | undefined): string {
  const d = parseLocalDate(str)
  if (!d) return '—'
  return d.toLocaleDateString('es-CL', { day: 'numeric', month: 'short', year: 'numeric' })
}

function activityDateRange(act: ProjectActivity): string {
  const s = parseLocalDate(act.start_date)
  const e = parseLocalDate(act.end_date)
  if (s && e) {
    const fmt = (d: Date) => d.toLocaleDateString('es-CL', { day: 'numeric', month: 'short', year: '2-digit' })
    return `${fmt(s)} → ${fmt(e)}`
  }
  return `M${act.start_month} → M${act.end_month}`
}

// ── Total months para selector ────────────────────────────────────────────────
const totalMonths = computed(() => {
  const proj = selectedProject.value
  const s = parseLocalDate(proj?.start_date)
  const e = parseLocalDate(proj?.end_date)
  if (s && e) {
    const m = (e.getFullYear() - s.getFullYear()) * 12 + e.getMonth() - s.getMonth() + 1
    if (m > 0) return m
  }
  if (!activities.value.length) return 36
  return Math.max(...activities.value.map(a => a.end_month || 1), 36)
})

const monthOptions = computed(() => {
  const start = parseLocalDate(selectedProject.value?.start_date)
  if (!start) return Array.from({ length: 60 }, (_, i) => ({ value: i + 1, label: `Mes ${i + 1}` }))
  return Array.from({ length: totalMonths.value }, (_, i) => {
    const d = new Date(start.getFullYear(), start.getMonth() + i)
    const label = d.toLocaleDateString('es-CL', { month: 'short', year: 'numeric' })
    return { value: i + 1, label: label.charAt(0).toUpperCase() + label.slice(1) }
  })
})

// ── Add activity form ─────────────────────────────────────────────────────────
const addForm  = ref({ description: '', start_month: 1, end_month: 1 })
const saving   = ref(false)

async function createActivity() {
  if (!selectedProjectId.value || !addForm.value.description.trim()) return
  saving.value = true
  try {
    await projectActivitiesApi.create({
      project_id:   selectedProjectId.value,
      description:  addForm.value.description,
      start_month:  addForm.value.start_month,
      end_month:    addForm.value.end_month,
      sort_order:   activities.value.length,
    })
    addForm.value = { description: '', start_month: addForm.value.start_month, end_month: addForm.value.end_month }
    showAddForm.value = false
    await loadActivities()
    ganttRef.value?.reload()
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
    await loadActivities()
    ganttRef.value?.reload()
  } catch {
    error.value = 'Error al eliminar'
  }
}

// ── RACI panel ────────────────────────────────────────────────────────────────
const showRaciPanel   = ref(false)
const raciActivityId  = ref<number | null>(null)
const raciActivityDesc = ref('')
const responsibilities = ref<ResponsibilityAssignment[]>([])
const raciForm        = ref({ member_id: null as number | null, raci_role: 'R' })
const savingRaci      = ref(false)

async function openRaci(act: ProjectActivity) {
  raciActivityId.value  = act.id
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

// ── Style helpers ─────────────────────────────────────────────────────────────
const statusLabel: Record<string, string> = {
  pending: 'Pendiente', in_progress: 'En curso', done: 'Terminada', blocked: 'Bloqueada',
}
const statusBadge: Record<string, string> = {
  pending: 'bg-slate-100 text-slate-600',
  in_progress: 'bg-blue-100 text-blue-700',
  done: 'bg-emerald-100 text-emerald-700',
  blocked: 'bg-red-100 text-red-700',
}
const statusDot: Record<string, string> = {
  pending: 'bg-slate-400', in_progress: 'bg-blue-500', done: 'bg-emerald-500', blocked: 'bg-red-500',
}
const raciColors: Record<string, string> = {
  R: 'bg-blue-100 text-blue-700', A: 'bg-amber-100 text-amber-700',
  C: 'bg-purple-100 text-purple-700', I: 'bg-slate-100 text-slate-600',
}
</script>

<template>
  <div class="flex flex-col h-full bg-gray-50">

    <!-- ── Header ────────────────────────────────────────────────────────── -->
    <div class="bg-white border-b border-gray-200 px-5 py-2.5 flex items-center gap-3">
      <h1 class="text-base font-bold text-gray-900 shrink-0">Planificación</h1>

      <!-- Tab switcher -->
      <GuideLabel text="Cambia entre vista de proyecto individual y vista global de todos los proyectos" position="bottom">
        <div class="flex items-center gap-0.5 bg-gray-100 rounded-lg p-0.5">
          <button
            class="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors"
            :class="activeTab === 'project' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
            @click="activeTab = 'project'"
          >
            <List class="w-3.5 h-3.5" /> Por proyecto
          </button>
          <button
            class="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors"
            :class="activeTab === 'global' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
            @click="activeTab = 'global'"
          >
            <BarChart2 class="w-3.5 h-3.5" /> Vista global
          </button>
        </div>
      </GuideLabel>

      <!-- Project selector -->
      <template v-if="activeTab === 'project'">
        <GuideLabel text="Elige el proyecto para ver su Gantt interactivo con drag & drop y dependencias" position="bottom">
          <select
            v-model="selectedProjectId"
            class="flex-1 min-w-0 max-w-sm border border-gray-200 rounded-lg px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option :value="null">Seleccionar proyecto…</option>
            <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.title }}</option>
          </select>
        </GuideLabel>

        <!-- Project date chip -->
        <div v-if="selectedProject?.start_date" class="flex items-center gap-1 text-xs text-gray-500 shrink-0">
          <Calendar class="w-3.5 h-3.5" />
          <span>{{ fmtDate(selectedProject.start_date) }} → {{ fmtDate(selectedProject.end_date) }}</span>
        </div>
      </template>

      <!-- Botones Vista Global -->
      <template v-if="activeTab === 'global'">
        <div class="ml-auto flex items-center gap-1 shrink-0">
          <AppTooltip text="Expandir todos los proyectos" position="bottom">
            <button
              class="flex items-center gap-1 text-gray-500 hover:text-gray-800 hover:bg-gray-100 px-2 py-1.5 rounded-lg text-xs font-medium transition-colors"
              @click="globalGanttRef?.expandAllProjects()"
            >
              <ChevronsUpDown class="w-3.5 h-3.5" />
              Expandir
            </button>
          </AppTooltip>
          <AppTooltip text="Contraer todos los proyectos" position="bottom">
            <button
              class="flex items-center gap-1 text-gray-500 hover:text-gray-800 hover:bg-gray-100 px-2 py-1.5 rounded-lg text-xs font-medium transition-colors"
              @click="globalGanttRef?.collapseAllProjects()"
            >
              <ChevronsDownUp class="w-3.5 h-3.5" />
              Contraer
            </button>
          </AppTooltip>
        </div>
      </template>

      <!-- Botones Gantt (solo en tab proyecto con proyecto seleccionado) -->
      <template v-if="activeTab === 'project' && selectedProjectId">
        <div class="ml-auto flex items-center gap-1 shrink-0">
          <AppTooltip text="Expandir todas las tareas del Gantt" position="bottom">
            <button
              class="flex items-center gap-1 text-gray-500 hover:text-gray-800 hover:bg-gray-100 px-2 py-1.5 rounded-lg text-xs font-medium transition-colors"
              @click="ganttRef?.expandAll()"
            >
              <ChevronsUpDown class="w-3.5 h-3.5" />
              Expandir
            </button>
          </AppTooltip>
          <AppTooltip text="Contraer todas las tareas al nivel superior" position="bottom">
            <button
              class="flex items-center gap-1 text-gray-500 hover:text-gray-800 hover:bg-gray-100 px-2 py-1.5 rounded-lg text-xs font-medium transition-colors"
              @click="ganttRef?.collapseAll()"
            >
              <ChevronsDownUp class="w-3.5 h-3.5" />
              Contraer
            </button>
          </AppTooltip>
          <GuideLabel text="Agrega una nueva tarea al proyecto seleccionado" position="bottom">
            <button
              class="flex items-center gap-1.5 bg-blue-600 text-white px-3 py-1.5 rounded-lg text-xs font-semibold hover:bg-blue-700 transition-colors"
              @click="showAddForm = !showAddForm"
            >
              <Plus class="w-3.5 h-3.5" />
              Nueva actividad
            </button>
          </GuideLabel>
        </div>
      </template>
    </div>

    <!-- Error bar -->
    <div
      v-if="error"
      class="mx-5 mt-3 flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-2.5 text-sm"
    >
      <AlertCircle class="w-4 h-4 shrink-0" />
      {{ error }}
      <button class="ml-auto text-red-400 hover:text-red-600" @click="error = null">
        <X class="w-4 h-4" />
      </button>
    </div>

    <!-- ── Add form (collapsible) ─────────────────────────────────────────── -->
    <Transition name="slide">
      <div
        v-if="showAddForm && activeTab === 'project' && selectedProjectId"
        class="bg-blue-50 border-b border-blue-100 px-5 py-3"
      >
        <div class="flex items-end gap-3 flex-wrap">
          <div class="flex-1 min-w-48">
            <label class="block text-xs font-medium text-blue-700 mb-1">Descripción *</label>
            <input
              v-model="addForm.description"
              type="text"
              placeholder="Descripción de la actividad"
              class="w-full border border-blue-200 rounded-lg px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              @keyup.enter="createActivity"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-blue-700 mb-1">Mes inicio</label>
            <select
              v-model.number="addForm.start_month"
              class="border border-blue-200 rounded-lg px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option v-for="opt in monthOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-blue-700 mb-1">Mes fin</label>
            <select
              v-model.number="addForm.end_month"
              class="border border-blue-200 rounded-lg px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option
                v-for="opt in monthOptions.filter(o => o.value >= addForm.start_month)"
                :key="opt.value"
                :value="opt.value"
              >{{ opt.label }}</option>
            </select>
          </div>
          <div class="flex gap-2">
            <button
              class="flex items-center gap-1.5 bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40 transition-colors"
              :disabled="saving || !addForm.description.trim()"
              @click="createActivity"
            >
              <Plus class="w-3.5 h-3.5" />
              {{ saving ? 'Guardando…' : 'Crear' }}
            </button>
            <button class="p-1.5 text-blue-400 hover:text-blue-600" @click="showAddForm = false">
              <X class="w-4 h-4" />
            </button>
          </div>
        </div>
        <p v-if="!selectedProject?.start_date" class="text-xs text-amber-600 mt-2">
          ⚠ El proyecto no tiene fecha de inicio — los meses se muestran como Mes 1, Mes 2…
        </p>
      </div>
    </Transition>

    <!-- ── GLOBAL TAB ─────────────────────────────────────────────────────── -->
    <div v-if="activeTab === 'global'" class="flex-1 min-h-0 overflow-hidden">
      <ProjectsGantt ref="globalGanttRef" />
    </div>

    <!-- ── PROJECT TAB ────────────────────────────────────────────────────── -->
    <template v-else>
      <!-- Empty state -->
      <div v-if="!selectedProjectId" class="flex-1 flex items-center justify-center">
        <div class="text-center text-gray-400">
          <Calendar class="w-14 h-14 mx-auto mb-3 opacity-20" />
          <p class="text-lg font-medium">Selecciona un proyecto</p>
          <p class="text-sm mt-1">El Gantt interactivo aparecerá aquí</p>
        </div>
      </div>

      <div v-else class="flex flex-1 min-h-0">

        <!-- ── LEFT: lista de actividades ──────────────────────────────────── -->
        <div class="w-72 shrink-0 bg-white border-r border-gray-200 flex flex-col">
          <!-- Header lista -->
          <div class="px-4 py-2.5 border-b border-gray-100 flex items-center justify-between">
            <span class="text-xs font-semibold text-gray-600 uppercase tracking-wide">
              Actividades
              <span class="ml-1 text-gray-400 font-normal">({{ activities.length }})</span>
            </span>
          </div>

          <!-- Loading -->
          <div v-if="loading" class="flex-1 flex items-center justify-center">
            <div class="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>

          <!-- Empty -->
          <div v-else-if="activities.length === 0" class="flex-1 flex items-center justify-center text-gray-400 text-sm p-6 text-center">
            Sin actividades. Usa el botón "Nueva actividad" arriba.
          </div>

          <!-- Activity list -->
          <div v-else class="flex-1 overflow-y-auto">
            <div
              v-for="act in activities"
              :key="act.id"
              class="px-3 py-2.5 border-b border-gray-50 hover:bg-gray-50 group transition-colors"
            >
              <div class="flex items-start gap-2">
                <!-- Status dot + number -->
                <div class="flex flex-col items-center gap-1 shrink-0 pt-0.5">
                  <div class="w-2 h-2 rounded-full" :class="statusDot[act.status] ?? 'bg-slate-400'" />
                  <span class="text-[10px] text-gray-300 font-mono leading-none">
                    {{ act.number != null ? `#${act.number}` : '' }}
                  </span>
                </div>

                <div class="flex-1 min-w-0">
                  <p class="text-xs font-medium text-gray-800 line-clamp-2 leading-snug">{{ act.description }}</p>
                  <!-- Dates -->
                  <p class="text-[11px] text-gray-400 mt-0.5 font-mono">{{ activityDateRange(act) }}</p>
                  <!-- Status + progress -->
                  <div class="flex items-center gap-2 mt-1.5">
                    <span class="text-[10px] rounded-full px-1.5 py-0.5 font-semibold" :class="statusBadge[act.status]">
                      {{ statusLabel[act.status] }}
                    </span>
                    <div class="flex-1 h-1 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        class="h-full rounded-full transition-all"
                        :class="act.status === 'done' ? 'bg-emerald-500' : 'bg-blue-500'"
                        :style="{ width: act.progress + '%' }"
                      />
                    </div>
                    <span class="text-[10px] text-gray-400 shrink-0">{{ act.progress }}%</span>
                  </div>
                </div>

                <!-- Hover actions -->
                <div class="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                  <AppTooltip text="Ver responsables RACI" position="left">
                    <button class="p-1 text-gray-300 hover:text-purple-600 rounded" @click="openRaci(act)">
                      <Users class="w-3 h-3" />
                    </button>
                  </AppTooltip>
                  <AppTooltip text="Eliminar actividad" position="left">
                    <button class="p-1 text-gray-300 hover:text-red-500 rounded" @click="deleteActivity(act.id)">
                      <Trash2 class="w-3 h-3" />
                    </button>
                  </AppTooltip>
                </div>
              </div>
            </div>
          </div>

          <!-- Leyenda estados -->
          <div class="px-3 py-2 border-t border-gray-100 flex items-center gap-3 flex-wrap">
            <div v-for="[cls, lbl] in [['bg-slate-400','Pend.'],['bg-blue-500','Curso'],['bg-emerald-500','Listo'],['bg-red-500','Bloq.']]"
              :key="lbl" class="flex items-center gap-1">
              <div class="w-2 h-2 rounded-full" :class="cls" />
              <span class="text-[10px] text-gray-500">{{ lbl }}</span>
            </div>
          </div>
        </div>

        <!-- ── RIGHT: DHTMLX Gantt ─────────────────────────────────────────── -->
        <div class="flex-1 min-w-0 overflow-hidden">
          <DHMLXGantt
            ref="ganttRef"
            :project-id="selectedProjectId"
            :project-start-date="selectedProject?.start_date ?? null"
            :project-end-date="selectedProject?.end_date ?? null"
            @task-click="openStatusModal"
            @refresh="loadActivities"
          />
        </div>
      </div>
    </template>

    <!-- ── ActivityStatusModal ────────────────────────────────────────────── -->
    <ActivityStatusModal
      :activity="statusModalActivity"
      @close="statusModalActivity = null"
      @save="saveStatus"
    />

    <!-- ── RACI Panel ─────────────────────────────────────────────────────── -->
    <Teleport to="body">
      <div
        v-if="showRaciPanel"
        class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4"
        @click.self="showRaciPanel = false"
      >
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md">
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
            <div>
              <h2 class="text-base font-semibold text-gray-900">Responsables RACI</h2>
              <p class="text-xs text-gray-500 mt-0.5 line-clamp-1">{{ raciActivityDesc }}</p>
            </div>
            <AppTooltip text="Cerrar" position="left">
              <button class="text-gray-400 hover:text-gray-600" @click="showRaciPanel = false">
                <X class="w-5 h-5" />
              </button>
            </AppTooltip>
          </div>
          <div class="p-5 space-y-4">
            <div v-if="responsibilities.length === 0" class="text-sm text-gray-400 text-center py-4">
              Sin asignaciones
            </div>
            <div v-else class="space-y-2">
              <div
                v-for="r in responsibilities"
                :key="r.id"
                class="flex items-center gap-3 rounded-xl border border-gray-100 px-3 py-2.5"
              >
                <span class="text-xs font-bold rounded px-1.5 py-0.5" :class="raciColors[r.raci_role]">
                  {{ r.raci_role }}
                </span>
                <span class="flex-1 text-sm text-gray-700">{{ r.member_name ?? '—' }}</span>
                <button class="text-gray-300 hover:text-red-500" @click="removeRaci(r.id)">
                  <X class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
            <div class="border-t border-gray-100 pt-4 space-y-3">
              <p class="text-sm font-medium text-gray-700">Agregar responsable</p>
              <div class="flex gap-2">
                <input
                  v-model.number="raciForm.member_id"
                  type="number"
                  placeholder="ID del miembro"
                  class="flex-1 border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <select
                  v-model="raciForm.raci_role"
                  class="border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="R">R — Responsible</option>
                  <option value="A">A — Accountable</option>
                  <option value="C">C — Consulted</option>
                  <option value="I">I — Informed</option>
                </select>
                <button
                  class="bg-blue-600 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                  :disabled="savingRaci || !raciForm.member_id"
                  @click="addRaci"
                >
                  <Plus class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
}
.slide-enter-to,
.slide-leave-from {
  max-height: 200px;
  opacity: 1;
}
</style>
