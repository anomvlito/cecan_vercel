<script setup lang="ts">
import { computed } from 'vue'
import type { ProjectActivity } from '@/types/publication'

const props = defineProps<{
  activities: ProjectActivity[]
  totalMonths?: number
  onActivityClick?: (activity: ProjectActivity) => void
}>()

const emit = defineEmits<{
  activityClick: [activity: ProjectActivity]
}>()

const total = computed(() => {
  if (props.totalMonths) return props.totalMonths
  if (!props.activities.length) return 12
  return Math.max(...props.activities.map(a => a.end_month || 1), 12) + 1
})

const monthLabels = computed(() => {
  return Array.from({ length: total.value }, (_, i) => `M${i + 1}`)
})

function getBarStyle(activity: ProjectActivity): Record<string, string> {
  if (!activity.start_month || !activity.end_month) return { display: 'none' }
  const t = total.value
  const left = ((activity.start_month - 1) / t) * 100
  const width = Math.max(((activity.end_month - activity.start_month + 1) / t) * 100, 2)
  return {
    left: `${left}%`,
    width: `${width}%`,
  }
}

function getProgressStyle(activity: ProjectActivity): Record<string, string> {
  return { width: `${activity.progress}%` }
}

const barColorClass: Record<string, string> = {
  pending:     'bg-gray-400',
  in_progress: 'bg-blue-500',
  done:        'bg-green-500',
  blocked:     'bg-red-500',
}

const statusDotClass: Record<string, string> = {
  pending:     'bg-gray-400',
  in_progress: 'bg-blue-500',
  done:        'bg-green-500',
  blocked:     'bg-red-500',
}

function handleBarClick(activity: ProjectActivity) {
  emit('activityClick', activity)
  props.onActivityClick?.(activity)
}

const colWidth = computed(() => `${(100 / total.value).toFixed(4)}%`)
</script>

<template>
  <div class="w-full select-none">
    <!-- Header row: month labels -->
    <div class="flex border-b border-gray-200 bg-gray-50">
      <!-- Left gutter to align with activity rows -->
      <div class="w-7 flex-shrink-0" />
      <!-- Month columns -->
      <div class="flex-1 relative flex">
        <div
          v-for="label in monthLabels"
          :key="label"
          class="text-center text-xs text-gray-400 font-medium py-1 border-r border-gray-100 last:border-r-0 truncate"
          :style="{ width: colWidth }"
        >
          {{ label }}
        </div>
      </div>
      <!-- Right gutter -->
      <div class="w-4 flex-shrink-0" />
    </div>

    <!-- Activity rows -->
    <div v-if="activities.length === 0" class="py-6 text-center text-sm text-gray-400">
      Sin actividades
    </div>

    <div
      v-for="activity in activities"
      :key="activity.id"
      class="flex items-center gap-1 py-0.5 hover:bg-gray-50 group"
    >
      <!-- Number circle -->
      <div
        class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
        :class="activity.number != null ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'"
      >
        {{ activity.number != null ? activity.number : '?' }}
      </div>

      <!-- Bar container -->
      <div class="flex-1 relative h-6 bg-gray-50 rounded overflow-hidden">
        <!-- Grid lines -->
        <div class="absolute inset-0 flex pointer-events-none">
          <div
            v-for="n in total"
            :key="n"
            class="h-full border-r border-gray-100 last:border-r-0"
            :style="{ width: colWidth }"
          />
        </div>

        <!-- Colored bar -->
        <div
          v-if="activity.start_month && activity.end_month"
          class="absolute top-0.5 bottom-0.5 rounded cursor-pointer transition-opacity hover:opacity-80"
          :class="barColorClass[activity.status] ?? 'bg-gray-400'"
          :style="getBarStyle(activity)"
          :title="activity.description"
          @click="handleBarClick(activity)"
        >
          <!-- Progress overlay (white, semi-transparent strip from left) -->
          <div
            class="absolute inset-y-0 left-0 bg-white/30 rounded-l"
            :style="getProgressStyle(activity)"
          />
        </div>
      </div>

      <!-- Status dot -->
      <div
        class="w-3 h-3 rounded-full flex-shrink-0"
        :class="statusDotClass[activity.status] ?? 'bg-gray-400'"
        :title="activity.status"
      />
    </div>

    <!-- Legend -->
    <div class="flex items-center gap-4 mt-3 pt-2 border-t border-gray-100 flex-wrap">
      <span class="text-xs text-gray-400 font-medium">Leyenda:</span>
      <div class="flex items-center gap-1.5">
        <div class="w-3 h-3 rounded bg-gray-400" />
        <span class="text-xs text-gray-500">Pendiente</span>
      </div>
      <div class="flex items-center gap-1.5">
        <div class="w-3 h-3 rounded bg-blue-500" />
        <span class="text-xs text-gray-500">En curso</span>
      </div>
      <div class="flex items-center gap-1.5">
        <div class="w-3 h-3 rounded bg-green-500" />
        <span class="text-xs text-gray-500">Terminada</span>
      </div>
      <div class="flex items-center gap-1.5">
        <div class="w-3 h-3 rounded bg-red-500" />
        <span class="text-xs text-gray-500">Bloqueada</span>
      </div>
    </div>
  </div>
</template>
