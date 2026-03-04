<template>
  <div
    class="bg-white rounded-2xl border-2 border-dashed shadow-sm p-10 text-center transition-colors cursor-pointer"
    :class="isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'"
    @dragover.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="onDrop"
    @click="fileInput?.click()"
  >
    <input
      ref="fileInput"
      type="file"
      accept=".pdf,application/pdf"
      class="hidden"
      @change="onInputChange"
    />

    <div class="flex flex-col items-center gap-4">
      <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
        <Upload class="w-8 h-8 text-blue-600" />
      </div>

      <div>
        <p class="text-lg font-semibold text-gray-800">
          {{ isDragging ? 'Suelta el PDF aquí' : 'Arrastra tu PDF aquí' }}
        </p>
        <p class="text-sm text-gray-400 mt-1">o haz clic para seleccionar un archivo</p>
      </div>

      <div class="flex items-center gap-2 text-xs text-gray-400">
        <FileText class="w-4 h-4" />
        <span>Solo archivos PDF · Máximo 50 MB</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Upload, FileText } from 'lucide-vue-next'

const emit = defineEmits<{
  fileSelected: [file: File]
}>()

const isDragging = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

function onDrop(event: DragEvent): void {
  isDragging.value = false
  const file = event.dataTransfer?.files[0]
  if (file) emitIfPdf(file)
}

function onInputChange(event: Event): void {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) emitIfPdf(file)
}

function emitIfPdf(file: File): void {
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    alert('Solo se aceptan archivos PDF')
    return
  }
  emit('fileSelected', file)
}
</script>
