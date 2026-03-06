<script setup lang="ts">
import { HelpCircle } from 'lucide-vue-next'
import { useGuideStore } from '@/stores/guide'

const props = withDefaults(defineProps<{
  text: string
  position?: 'top' | 'bottom' | 'left' | 'right'
}>(), {
  position: 'bottom',
})

const guideStore = useGuideStore()

const positionClasses: Record<string, string> = {
  top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
  bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
  left: 'right-full top-1/2 -translate-y-1/2 mr-2',
  right: 'left-full top-1/2 -translate-y-1/2 ml-2',
}

const arrowClasses: Record<string, string> = {
  top: 'top-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent border-t-blue-800',
  bottom: 'bottom-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent border-b-blue-800',
  left: 'left-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent border-l-blue-800',
  right: 'right-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent border-r-blue-800',
}
</script>

<template>
  <div class="relative inline-flex">
    <slot />
    <Transition name="guide-fade">
      <div
        v-if="guideStore.active"
        :class="['absolute z-50 pointer-events-none', positionClasses[props.position]]"
      >
        <!-- Flecha -->
        <div
          :class="['absolute w-0 h-0 border-4', arrowClasses[props.position]]"
        />
        <!-- Etiqueta -->
        <div class="flex items-start gap-1.5 bg-blue-900/90 border border-blue-600 text-white text-xs rounded-lg px-2.5 py-2 shadow-lg backdrop-blur-sm max-w-[220px] whitespace-normal">
          <HelpCircle class="w-3.5 h-3.5 text-blue-300 flex-shrink-0 mt-px" />
          <span class="leading-snug">{{ props.text }}</span>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.guide-fade-enter-active,
.guide-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.guide-fade-enter-from,
.guide-fade-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
