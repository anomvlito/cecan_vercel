<script setup lang="ts">
import { RouterLink, useRoute } from 'vue-router'
import { BookOpen, Upload, FlaskConical, BookMarked } from 'lucide-vue-next'

const route = useRoute()

const navItems = [
  { to: '/publications', icon: BookOpen, label: 'Publicaciones' },
  { to: '/upload', icon: Upload, label: 'Subir PDF' },
  { to: '/journals', icon: BookMarked, label: 'Revistas JCR' },
]
</script>

<template>
  <aside class="w-56 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col">
    <!-- Brand -->
    <div class="h-16 flex items-center px-5 border-b border-gray-200">
      <FlaskConical class="w-6 h-6 text-blue-600 mr-2" />
      <span class="text-lg font-bold text-gray-900">CECAN</span>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 py-4 px-3 space-y-1">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
        :class="
          route.path === item.to
            ? 'bg-blue-50 text-blue-700'
            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
        "
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
