<template>
  <div class="flex justify-between items-center py-1 border-b border-gray-50 last:border-0">
    <span class="text-gray-400 font-medium">{{ label }}</span>
    <span class="text-gray-700">{{ value }}</span>
  </div>
</template>

<script setup lang="ts">
defineProps<{ label: string; value: string }>()
</script>
