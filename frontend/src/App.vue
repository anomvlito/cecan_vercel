<script setup lang="ts">
import { ref } from 'vue'
import { RouterView } from 'vue-router'
import { Menu } from 'lucide-vue-next'
import Sidebar from '@/components/layout/Sidebar.vue'

const sidebarOpen = ref(false)
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-gray-50">
    <Sidebar :open="sidebarOpen" @close="sidebarOpen = false" />

    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
      <!-- Top bar mobile -->
      <div class="md:hidden flex items-center h-14 px-4 bg-white border-b border-gray-200 flex-shrink-0">
        <button
          class="p-2 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors"
          @click="sidebarOpen = true"
        >
          <Menu class="w-5 h-5" />
        </button>
        <span class="ml-3 text-base font-bold text-gray-900">CECAN</span>
      </div>

      <main class="flex-1 overflow-hidden flex flex-col">
        <RouterView class="flex-1 h-full overflow-y-auto" />
      </main>
    </div>
  </div>
</template>
