<template>
  <div class="min-h-screen bg-gray-50 py-12 px-4">
    <div class="max-w-3xl mx-auto">
      <!-- Header -->
      <div class="mb-8 text-center">
        <h1 class="text-3xl font-bold text-gray-900">Subir Publicación</h1>
        <p class="mt-2 text-gray-500">
          Sube el PDF de tu publicación y extraeremos automáticamente el DOI y las métricas JCR.
        </p>
      </div>

      <!-- Drop Zone -->
      <DropZone
        v-if="state === 'idle'"
        @file-selected="onFileSelected"
      />

      <!-- Uploading State -->
      <div
        v-else-if="state === 'uploading'"
        class="bg-white rounded-2xl border border-gray-200 shadow-sm p-8 text-center"
      >
        <div class="flex justify-center mb-4">
          <div class="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
        </div>
        <p class="text-gray-600 font-medium">Procesando PDF...</p>
        <p class="text-sm text-gray-400 mt-1">Extrayendo DOI y consultando OpenAlex</p>
      </div>

      <!-- Result -->
      <UploadResult
        v-else-if="state === 'success' && result"
        :result="result"
        @upload-another="reset"
      />

      <!-- Error -->
      <div
        v-else-if="state === 'error'"
        class="bg-white rounded-2xl border border-red-200 shadow-sm p-8"
      >
        <div class="flex items-start gap-4">
          <div class="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center flex-shrink-0">
            <AlertCircle class="w-5 h-5 text-red-600" />
          </div>
          <div>
            <h3 class="font-semibold text-gray-900">Error al procesar el archivo</h3>
            <p class="text-sm text-gray-500 mt-1">{{ error }}</p>
            <button
              class="mt-4 text-sm font-medium text-blue-600 hover:underline"
              @click="reset"
            >
              Intentar de nuevo
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { AlertCircle } from 'lucide-vue-next'
import { useUploadPdf } from '@/composables/useUploadPdf'
import DropZone from '@/components/DropZone.vue'
import UploadResult from '@/components/UploadResult.vue'

const { state, result, error, upload, reset } = useUploadPdf()

function onFileSelected(file: File): void {
  upload(file)
}
</script>
