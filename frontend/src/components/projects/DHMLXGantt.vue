<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { gantt } from 'dhtmlx-gantt'
import 'dhtmlx-gantt/codebase/dhtmlxgantt.css'

// ── Props / Emits ─────────────────────────────────────────────────────────────
const props = defineProps<{
  projectId: number | null
  projectStartDate: string | null
  projectEndDate: string | null
}>()

const emit = defineEmits<{
  taskClick: [activityId: number]
  refresh: []
}>()

// ── Refs ──────────────────────────────────────────────────────────────────────
const ganttRef  = ref<HTMLElement | null>(null)
const g         = gantt as any   // las typedefs de dhtmlx-gantt tienen bugs conocidos
let initialized = false
let eventIds: string[] = []

// ── Locale español ────────────────────────────────────────────────────────────
const MONTH_SHORT = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
const MONTH_FULL  = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

function fmtDate(d: Date): string {
  return `${d.getDate()} ${MONTH_SHORT[d.getMonth()]} '${String(d.getFullYear()).slice(2)}`
}

// ── Inicialización ────────────────────────────────────────────────────────────
function initGantt() {
  if (!ganttRef.value || initialized) return
  initialized = true

  // Locale
  g.i18n.setLocale({
    date: {
      month_full:  MONTH_FULL,
      month_short: MONTH_SHORT,
      day_full:  ['Domingo','Lunes','Martes','Miércoles','Jueves','Viernes','Sábado'],
      day_short: ['Dom','Lun','Mar','Mié','Jue','Vie','Sáb'],
    },
    labels: {
      new_task: 'Nueva tarea',
      icon_save: 'Guardar', icon_cancel: 'Cancelar',
      icon_details: 'Detalles', icon_edit: 'Editar', icon_delete: 'Eliminar',
      confirm_closing: '', confirm_deleting: '¿Eliminar tarea?',
      section_description: 'Descripción', section_time: 'Período',
      link: 'Dependencia', confirm_link_deleting: '¿Eliminar dependencia?',
      link_start: ' (inicio)', link_end: ' (fin)',
      type_task: 'Tarea', type_project: 'Proyecto', type_milestone: 'Hito',
      minutes: 'Minutos', hours: 'Horas', days: 'Días',
      weeks: 'Semanas', months: 'Meses', years: 'Años',
    },
  })

  // ── Config ────────────────────────────────────────────────────────────────
  g.config.date_format            = '%Y-%m-%d %H:%i'
  g.config.row_height             = 34
  g.config.task_height            = 22
  g.config.min_column_width       = 40
  g.config.highlight_critical_path = true
  g.config.drag_links             = true
  g.config.drag_progress          = true

  // Escala: año + mes
  g.config.scales = [
    { unit: 'year',  step: 1, format: '%Y' },
    { unit: 'month', step: 1, format: (d: Date) => MONTH_SHORT[d.getMonth()] },
  ]

  // Columnas
  g.config.columns = [
    {
      name: 'text', label: 'Actividad', tree: true, width: 220,
      template: (task: any) => {
        const num = task.number != null
          ? `<span style="color:#94a3b8;font-size:10px;margin-right:3px">#${task.number}</span>`
          : ''
        return `${num}${task.text}`
      },
    },
    {
      name: 'start_date', label: 'Inicio', align: 'center', width: 82,
      template: (task: any) => (task.start_date ? fmtDate(task.start_date) : '—'),
    },
    { name: 'duration', label: 'Días', align: 'center', width: 48 },
    {
      name: 'progress_col', label: '%', align: 'center', width: 44,
      template: (task: any) => `${Math.round((task.progress ?? 0) * 100)}%`,
    },
  ]

  // ── Templates ─────────────────────────────────────────────────────────────
  g.templates.task_class = (_s: any, _e: any, task: any): string =>
    `cecan-task cecan-status-${task.status ?? 'pending'}`

  // Tooltip
  g.plugins({ tooltip: true, critical_path: true })
  g.templates.tooltip_text = (_s: any, _e: any, task: any): string => {
    const statusMap: Record<string, string> = {
      pending: 'Pendiente', in_progress: 'En curso', done: 'Terminada', blocked: 'Bloqueada',
    }
    const s = task.start_date ? fmtDate(task.start_date) : '—'
    const e = task.end_date   ? fmtDate(task.end_date)   : '—'
    return [
      `<b>${task.text}</b>`,
      `Estado: ${statusMap[task.status] ?? task.status}`,
      `Avance: ${Math.round((task.progress ?? 0) * 100)}%`,
      `${s} → ${e}`,
    ].join('<br/>')
  }

  // ── Init DOM ──────────────────────────────────────────────────────────────
  g.init(ganttRef.value)

  // ── Eventos ───────────────────────────────────────────────────────────────

  // Clic en tarea → abrir modal de estado
  eventIds.push(
    g.attachEvent('onTaskClick', (id: any) => {
      emit('taskClick', Number(id))
      return true
    }),
  )

  // Drag → actualizar start/end month
  eventIds.push(
    g.attachEvent('onAfterTaskDrag', async (id: any, mode: string) => {
      if (mode !== 'move' && mode !== 'resize') return
      const task = g.getTask(id)
      if (!task?.start_date || !task?.end_date) return
      const fmt = (d: Date) => {
        const y = d.getFullYear()
        const m = String(d.getMonth() + 1).padStart(2, '0')
        const day = String(d.getDate()).padStart(2, '0')
        return `${y}-${m}-${day}`
      }
      try {
        await fetch(`/api/gantt/task/${id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            start_date: fmt(task.start_date),
            end_date:   fmt(task.end_date),
          }),
        })
        emit('refresh')
      } catch (e) {
        console.error('Error al actualizar tarea:', e)
      }
    }),
  )

  // Crear dependencia
  eventIds.push(
    g.attachEvent('onAfterLinkAdd', async (_id: any, link: any) => {
      if (!props.projectId) return
      try {
        const res = await fetch('/api/gantt/links', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            project_id: props.projectId,
            source: Number(link.source),
            target: Number(link.target),
            type:   String(link.type ?? '0'),
          }),
        })
        if (res.ok) {
          const saved = await res.json()
          g.changeLinkId(link.id, saved.id)
        }
      } catch (e) {
        console.error('Error al crear dependencia:', e)
      }
    }),
  )

  // Eliminar dependencia
  eventIds.push(
    g.attachEvent('onAfterLinkDelete', async (id: any) => {
      try {
        await fetch(`/api/gantt/links/${id}`, { method: 'DELETE' })
      } catch (e) {
        console.error('Error al eliminar dependencia:', e)
      }
    }),
  )
}

// ── Cargar datos ──────────────────────────────────────────────────────────────
async function loadData() {
  if (!props.projectId || !initialized) return
  try {
    const res = await fetch(`/api/gantt/project/${props.projectId}`)
    if (!res.ok) return
    const data = await res.json()
    g.clearAll()
    g.parse(data)
  } catch (e) {
    console.error('Error al cargar Gantt:', e)
  }
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────
onMounted(() => {
  initGantt()
  loadData()
})

onBeforeUnmount(() => {
  eventIds.forEach(id => g.detachEvent(id))
  eventIds = []
  g.clearAll()
  initialized = false
})

watch(() => props.projectId, (v) => { if (v) loadData() })

function expandAll() {
  g.eachTask((task: any) => { g.open(task.id) })
}

function collapseAll() {
  g.eachTask((task: any) => { g.close(task.id) })
}

defineExpose({ reload: loadData, expandAll, collapseAll })
</script>

<template>
  <div ref="ganttRef" class="w-full h-full" />
</template>

<style>
/* ── Estado de barras ─────────────────────────────────────────────────────── */
.cecan-status-pending     .gantt_task_content { background: #94a3b8; border-color: #64748b; }
.cecan-status-in_progress .gantt_task_content { background: #3b82f6; border-color: #1d4ed8; }
.cecan-status-done        .gantt_task_content { background: #22c55e; border-color: #15803d; }
.cecan-status-blocked     .gantt_task_content { background: #ef4444; border-color: #b91c1c; }

.cecan-status-pending     .gantt_task_progress { background: #475569; }
.cecan-status-in_progress .gantt_task_progress { background: #1d4ed8; }
.cecan-status-done        .gantt_task_progress { background: #15803d; }
.cecan-status-blocked     .gantt_task_progress { background: #991b1b; }

/* ── Ruta crítica ─────────────────────────────────────────────────────────── */
.gantt_critical_task .gantt_task_content  { outline: 2px solid #dc2626 !important; }
.gantt_critical_link .gantt_line_wrapper div { background: #dc2626 !important; }

/* ── Refinamientos visuales ──────────────────────────────────────────────── */
.gantt_task_line      { border-radius: 5px; }
.gantt_task_content   { border-radius: 5px; font-size: 11px; font-weight: 600; letter-spacing: 0.01em; }
.gantt_grid_head_cell { font-size: 11px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; }
.gantt_cell           { font-size: 12px; color: #374151; }
.gantt_tooltip        { font-size: 12px; line-height: 1.6; border-radius: 10px; padding: 10px 14px; box-shadow: 0 4px 20px rgba(0,0,0,.15); }
.gantt_scale_cell     { font-size: 11px; font-weight: 500; }

/* ── Hover y selección ────────────────────────────────────────────────────── */
.gantt_row:hover { background: #f0f9ff !important; }
.gantt_row.gantt_selected { background: #eff6ff !important; }
.gantt_task_row:hover { background: #f0f9ff !important; }
.gantt_task_row.gantt_selected { background: #eff6ff !important; }
</style>
