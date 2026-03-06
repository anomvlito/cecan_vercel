<script setup lang="ts">
import { RouterLink, useRoute } from 'vue-router'
import { BookOpen, Upload, FlaskConical, BookMarked, Users, GraduationCap, FolderOpen, X, Globe } from 'lucide-vue-next'

defineProps<{ open: boolean }>()
defineEmits<{ close: [] }>()

const route = useRoute()

const navItems = [
  { to: '/', icon: Globe, label: 'Mapa 3D' },
  { to: '/publications', icon: BookOpen, label: 'Publicaciones' },
  { to: '/upload', icon: Upload, label: 'Subir PDF' },
  { to: '/journals', icon: BookMarked, label: 'Revistas JCR' },
  { to: '/researchers', icon: Users, label: 'Investigadores' },
  { to: '/students', icon: GraduationCap, label: 'Estudiantes' },
  { to: '/projects', icon: FolderOpen, label: 'Proyectos' },
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
    <!-- Brand -->
    <div class="h-16 flex items-center justify-between px-5 border-b border-gray-200">
      <div class="flex items-center gap-2">
        <FlaskConical class="w-6 h-6 text-blue-600" />
        <span class="text-lg font-bold text-gray-900">CECAN</span>
      </div>
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
          (item.to === '/' ? route.path === '/' : route.path.startsWith(item.to))
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
    <div class="px-5 py-4 border-t border-gray-200">
      <p class="text-xs text-gray-400">Plataforma CECAN</p>
    </div>
  </aside>
</template>
