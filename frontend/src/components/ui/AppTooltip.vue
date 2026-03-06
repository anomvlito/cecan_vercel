<script setup lang="ts">
withDefaults(defineProps<{
  text: string
  position?: 'top' | 'bottom' | 'left' | 'right'
}>(), {
  position: 'top',
})
</script>

<template>
  <div class="relative inline-flex group">
    <slot />
    <div
      :class="[
        'absolute z-50 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-150',
        position === 'top' && 'bottom-full left-1/2 -translate-x-1/2 mb-1.5',
        position === 'bottom' && 'top-full left-1/2 -translate-x-1/2 mt-1.5',
        position === 'left' && 'right-full top-1/2 -translate-y-1/2 mr-1.5',
        position === 'right' && 'left-full top-1/2 -translate-y-1/2 ml-1.5',
      ]"
    >
      <div class="bg-gray-900 text-white text-xs rounded-md px-2 py-1 whitespace-nowrap shadow-md">
        {{ text }}
      </div>
    </div>
  </div>
</template>
