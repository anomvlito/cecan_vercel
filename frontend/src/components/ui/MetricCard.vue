<template>
  <div class="bg-gray-50 rounded-xl p-4">
    <p class="text-xs text-gray-400 font-medium uppercase tracking-wide mb-1">{{ label }}</p>
    <p
      class="text-2xl font-bold"
      :class="[badgeColor ? `inline-flex items-center px-2 py-0.5 rounded text-sm font-semibold ${badgeColor}` : 'text-gray-800']"
    >
      {{ value }}
    </p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  value: string
  badgeColor?: string
  icon?: string
}>()
</script>
