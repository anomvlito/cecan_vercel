<script setup lang="ts">
import { computed } from 'vue'
import type { ProjectActivity } from '@/types/publication'

const props = defineProps<{
  activities: ProjectActivity[]
  totalMonths?: number
  projectStartDate?: string | null  // ISO date — si se provee, etiquetas muestran mes/año real
}>()

const emit = defineEmits<{
  activityClick: [activity: ProjectActivity]
}>()

// ── Total de meses en el timeline ────────────────────────────────────────────
const total = computed(() => {
  if (props.totalMonths && props.totalMonths > 0) return props.totalMonths
  if (!props.activities.length) return 12
  return Math.max(...props.activities.map(a => a.end_month || 1), 12)
})

// ── Etiquetas de columnas ────────────────────────────────────────────────────
const monthLabels = computed(() => {
  if (props.projectStartDate) {
    const start = new Date(props.projectStartDate + 'T00:00:00')
    return Array.from({ length: total.value }, (_, i) => {
      const d = new Date(start.getFullYear(), start.getMonth() + i)
      return d.toLocaleDateString('es-CL', { month: 'short', year: '2-digit' })
    })
  }
  return Array.from({ length: total.value }, (_, i) => `M${i + 1}`)
})

// ── Índices de columnas donde cambia el año (para separador visual) ──────────
const yearChanges = computed<Set<number>>(() => {
  const set = new Set<number>()
  if (!props.projectStartDate) return set
  const start = new Date(props.projectStartDate + 'T00:00:00')
  for (let i = 1; i < total.value; i++) {
    const prev = new Date(start.getFullYear(), start.getMonth() + i - 1)
    const curr = new Date(start.getFullYear(), start.getMonth() + i)
    if (curr.getFullYear() !== prev.getFullYear()) set.add(i)
  }
  return set
})

// ── Posición de "Hoy" ────────────────────────────────────────────────────────
const todayLeft = computed<string | null>(() => {
  if (!props.projectStartDate) return null
  const start = new Date(props.projectStartDate + 'T00:00:00')
  const today = new Date()
  const monthsDiff =
    (today.getFullYear() - start.getFullYear()) * 12 +
    today.getMonth() -
    start.getMonth()
  const dayFraction =
    (today.getDate() - 1) /
    new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate()
  const pct = ((monthsDiff + dayFraction) / total.value) * 100
  if (pct < 0 || pct > 100) return null
  return `${pct.toFixed(2)}%`
})

// ── Ancho de columna ─────────────────────────────────────────────────────────
const colWidth = computed(() => `${(100 / total.value).toFixed(4)}%`)

// ── Estilo de barra (posicionamiento CSS) ────────────────────────────────────
function getBarStyle(activity: ProjectActivity): Record<string, string> {
  const sm = activity.start_month
  const em = activity.end_month
  if (!sm || !em) return { display: 'none' }
  const t = total.value
  const left = ((sm - 1) / t) * 100
  const width = Math.max(((em - sm + 1) / t) * 100, 2)
  return { left: `${left}%`, width: `${width}%` }
}

// ── Tooltip con info completa ────────────────────────────────────────────────
function barTitle(activity: ProjectActivity): string {
  const label = statusLabel[activity.status] ?? activity.status
  const dates =
    activity.start_date && activity.end_date
      ? `\n${fmt(activity.start_date)} → ${fmt(activity.end_date)}`
      : `\nM${activity.start_month} → M${activity.end_month}`
  return `${activity.description}\n${label} · ${activity.progress}%${dates}`
}

function fmt(iso: string): string {
  return new Date(iso + 'T00:00:00').toLocaleDateString('es-CL', {
    day: '2-digit', month: 'short', year: 'numeric',
  })
}

// ── Clases de color por estado ───────────────────────────────────────────────
const barColorClass: Record<string, string> = {
  pending:     'bg-gray-400',
  in_progress: 'bg-blue-500',
  done:        'bg-green-500',
  blocked:     'bg-red-500',
}
const statusLabel: Record<string, string> = {
  pending:     'Pendiente',
  in_progress: 'En curso',
  done:        'Terminada',
  blocked:     'Bloqueada',
}
</script>

<template>
  <div class="w-full select-none text-xs">

    <!-- ── Header de meses ───────────────────────────────────────────────── -->
    <div class="flex border-b border-gray-200 bg-gray-50 sticky top-0 z-10">
      <div class="w-7 flex-shrink-0" />
      <div class="flex-1 relative flex overflow-hidden">
        <div
          v-for="(label, i) in monthLabels"
          :key="i"
          class="text-center text-gray-400 font-medium py-1 truncate flex-shrink-0"
          :class="yearChanges.has(i) ? 'border-l-2 border-gray-300' : 'border-r border-gray-100'"
          :style="{ width: colWidth }"
        >
          {{ label }}
        </div>
        <!-- Línea "Hoy" en el header -->
        <div
          v-if="todayLeft"
          class="absolute top-0 bottom-0 w-px bg-red-400 z-20 pointer-events-none"
          :style="{ left: todayLeft }"
        />
      </div>
      <div class="w-4 flex-shrink-0" />
    </div>

    <!-- ── Filas de actividades ──────────────────────────────────────────── -->
    <div
      v-if="!activities.filter(a => a.start_month && a.end_month).length"
      class="py-8 text-center text-gray-400"
    >
      Sin actividades con meses definidos
    </div>

    <div
      v-for="activity in activities.filter(a => a.start_month && a.end_month)"
      :key="activity.id"
      class="flex items-center gap-1 py-0.5 hover:bg-gray-50 group"
    >
      <!-- Círculo con número -->
      <div
        class="w-6 h-6 rounded-full flex items-center justify-center font-bold flex-shrink-0 text-[10px]"
        :class="activity.number != null ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'"
      >
        {{ activity.number != null ? activity.number : '?' }}
      </div>

      <!-- Contenedor de barra -->
      <div class="flex-1 relative h-6 bg-gray-50 rounded overflow-hidden">

        <!-- Líneas de cuadrícula -->
        <div class="absolute inset-0 flex pointer-events-none">
          <div
            v-for="i in total"
            :key="i"
            class="h-full flex-shrink-0"
            :class="yearChanges.has(i - 1) ? 'border-l-2 border-gray-200' : 'border-r border-gray-100'"
            :style="{ width: colWidth }"
          />
        </div>

        <!-- Línea "Hoy" en filas -->
        <div
          v-if="todayLeft"
          class="absolute top-0 bottom-0 w-px bg-red-400/60 z-10 pointer-events-none"
          :style="{ left: todayLeft }"
        />

        <!-- Barra coloreada -->
        <div
          class="absolute top-0.5 bottom-0.5 rounded cursor-pointer transition-opacity hover:opacity-80 z-0 group-hover:z-10"
          :class="barColorClass[activity.status] ?? 'bg-gray-400'"
          :style="getBarStyle(activity)"
          :title="barTitle(activity)"
          @click="emit('activityClick', activity)"
        >
          <!-- Overlay de progreso (franja oscura sobre la barra) -->
          <div
            v-if="activity.progress > 0 && activity.status !== 'done'"
            class="absolute inset-y-0 left-0 bg-black/15 rounded-l"
            :style="{ width: `${activity.progress}%` }"
          />
          <!-- Etiqueta de progreso si hay espacio -->
          <span
            v-if="activity.progress > 0"
            class="absolute inset-y-0 right-1 flex items-center text-white font-semibold leading-none text-[10px] pointer-events-none"
          >
            {{ activity.progress }}%
          </span>
        </div>
      </div>

      <!-- Punto de estado -->
      <div
        class="w-2.5 h-2.5 rounded-full flex-shrink-0"
        :class="barColorClass[activity.status] ?? 'bg-gray-400'"
        :title="statusLabel[activity.status] ?? activity.status"
      />
    </div>

    <!-- ── Leyenda ────────────────────────────────────────────────────────── -->
    <div class="flex items-center gap-4 mt-3 pt-2 border-t border-gray-100 flex-wrap">
      <span class="text-gray-400 font-medium">Leyenda:</span>
      <div v-for="[cls, lbl] in [['bg-gray-400','Pendiente'],['bg-blue-500','En curso'],['bg-green-500','Terminada'],['bg-red-500','Bloqueada']]" :key="lbl" class="flex items-center gap-1.5">
        <div class="w-3 h-3 rounded" :class="cls" />
        <span class="text-gray-500">{{ lbl }}</span>
      </div>
      <div v-if="todayLeft" class="flex items-center gap-1.5">
        <div class="w-px h-3 bg-red-400" style="width:2px" />
        <span class="text-gray-500">Hoy</span>
      </div>
    </div>
  </div>
</template>
