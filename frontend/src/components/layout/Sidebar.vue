<script setup lang="ts">
import { RouterLink, useRoute } from 'vue-router'
import { Upload, FlaskConical, BookMarked, Users, GraduationCap, X, Network, GanttChartSquare, ClipboardList, BookOpen, HelpCircle } from 'lucide-vue-next'
import { useGuideStore } from '@/stores/guide'

defineProps<{ open: boolean }>()
defineEmits<{ close: [] }>()

const route = useRoute()
const guideStore = useGuideStore()

const navItems = [
  { to: '/publications', icon: BookOpen, label: 'Publicaciones' },
  { to: '/upload',       icon: Upload,          label: 'Subir PDF' },
  { to: '/journals',     icon: BookMarked,       label: 'Revistas JCR' },
  { to: '/researchers',  icon: Users,            label: 'Investigadores' },
  { to: '/students',     icon: GraduationCap,    label: 'Estudiantes' },
  { to: '/collaboration-map', icon: Network,     label: 'Mapa Colaboración' },
  { to: '/gantt',        icon: GanttChartSquare, label: 'Planificación' },
  { to: '/my-tasks',     icon: ClipboardList,    label: 'Mis Tareas' },
]
</script>

<template>
  <!-- Overlay mobile -->
  <div
    v-if="open"
    class="fixed inset-0 bg-black/40 z-20 md:hidden"
    @click="$emit('close')"
  />

  <!-- Sidebar -->
  <aside
    class="fixed md:static inset-y-0 left-0 z-30 w-56 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col transition-transform duration-200"
    :class="open ? 'translate-x-0' : '-translate-x-full md:translate-x-0'"
  >
    <!-- Brand — enlace al inicio -->
    <div class="h-16 flex items-center justify-between px-5 border-b border-gray-200">
      <RouterLink to="/" class="flex items-center gap-2 hover:opacity-80 transition-opacity" @click="$emit('close')">
        <FlaskConical class="w-6 h-6 text-blue-600" />
        <span class="text-lg font-bold text-gray-900">CECAN</span>
      </RouterLink>
      <!-- Botón cerrar en mobile -->
      <button class="md:hidden p-1 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100" @click="$emit('close')">
        <X class="w-5 h-5" />
      </button>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
        :class="
          route.path.startsWith(item.to)
            ? 'bg-blue-50 text-blue-700'
            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
        "
        @click="$emit('close')"
      >
        <component :is="item.icon" class="w-4 h-4 flex-shrink-0" />
        {{ item.label }}
      </RouterLink>
    </nav>

    <!-- Footer -->
    <div class="px-3 py-4 border-t border-gray-200 space-y-2">
      <button
        class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-colors"
        :class="guideStore.active
          ? 'bg-blue-50 text-blue-700 border border-blue-200'
          : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'"
        @click="guideStore.toggle()"
      >
        <HelpCircle class="w-4 h-4 flex-shrink-0" />
        {{ guideStore.active ? 'Desactivar leyendas' : 'Activar leyendas guía' }}
        <span v-if="guideStore.active" class="ml-auto w-2 h-2 rounded-full bg-blue-500" />
      </button>
      <p class="text-xs text-gray-400 px-3">Plataforma CECAN</p>
    </div>
  </aside>
</template>
