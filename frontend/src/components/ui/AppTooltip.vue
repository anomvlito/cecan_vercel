<script setup lang="ts">
import { ref } from 'vue'

withDefaults(defineProps<{
  text: string
  position?: 'top' | 'bottom' | 'left' | 'right'
  delay?: number
}>(), {
  position: 'top',
  delay: 400,
})

const visible = ref(false)
let showTimer: ReturnType<typeof setTimeout> | null = null

function onEnter() {
  // Delay antes de mostrar, evita flickers en hover rápido
  showTimer = setTimeout(() => { visible.value = true }, 400)
}

function onLeave() {
  if (showTimer) { clearTimeout(showTimer); showTimer = null }
  visible.value = false
}

function onPress() {
  // Ocultar inmediatamente al hacer click — evita solapamiento con modales/acciones
  if (showTimer) { clearTimeout(showTimer); showTimer = null }
  visible.value = false
}
</script>

<template>
  <div
    class="relative inline-flex"
    @mouseenter="onEnter"
    @mouseleave="onLeave"
    @mousedown="onPress"
    @focus="onEnter"
    @blur="onLeave"
  >
    <slot />
    <Transition name="tooltip-fade">
      <div
        v-if="visible"
        class="absolute z-[60] pointer-events-none"
        :class="{
          'bottom-full left-1/2 -translate-x-1/2 mb-1.5': position === 'top',
          'top-full left-1/2 -translate-x-1/2 mt-1.5': position === 'bottom',
          'right-full top-1/2 -translate-y-1/2 mr-1.5': position === 'left',
          'left-full top-1/2 -translate-y-1/2 ml-1.5': position === 'right',
        }"
      >
        <div class="bg-gray-900 text-white text-xs rounded-md px-2 py-1 whitespace-nowrap shadow-lg">
          {{ text }}
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.tooltip-fade-enter-active,
.tooltip-fade-leave-active {
  transition: opacity 0.1s ease;
}
.tooltip-fade-enter-from,
.tooltip-fade-leave-to {
  opacity: 0;
}
</style>
