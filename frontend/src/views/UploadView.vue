<template>
  <div class="min-h-screen bg-gray-50 py-12 px-4">
    <div class="max-w-3xl mx-auto">
      <!-- Header -->
      <div class="mb-8 text-center">
        <h1 class="text-3xl font-bold text-gray-900">Subir Publicación</h1>
        <p class="mt-2 text-gray-500">
          Sube uno o varios PDFs y extraeremos automáticamente el DOI y las métricas JCR.
        </p>
      </div>

      <!-- Drop Zone -->
      <DropZone @files-selected="onFilesSelected" />

      <!-- Jobs -->
      <div v-if="jobs.length > 0" class="mt-6 space-y-2">
        <div
          v-for="job in jobs"
          :key="job.id"
          class="rounded-xl border px-4 py-3 flex items-start gap-3 text-sm"
          :class="{
            'bg-blue-50 border-blue-200': job.state === 'uploading',
            'bg-green-50 border-green-200': job.state === 'success' && job.result?.journal_found,
            'bg-indigo-50 border-indigo-200': job.state === 'success' && job.result?.doi_found && !job.result?.journal_found,
            'bg-yellow-50 border-yellow-200': job.state === 'success' && !job.result?.doi_found,
            'bg-red-50 border-red-200': job.state === 'error',
          }"
        >
          <!-- Icono de estado -->
          <Loader2
            v-if="job.state === 'uploading'"
            class="w-4 h-4 text-blue-500 animate-spin flex-shrink-0 mt-0.5"
          />
          <CheckCircle
            v-else-if="job.state === 'success' && job.result?.journal_found"
            class="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5"
          />
          <Search
            v-else-if="job.state === 'success' && job.result?.doi_found && !job.result?.journal_found"
            class="w-4 h-4 text-indigo-500 flex-shrink-0 mt-0.5"
          />
          <AlertTriangle
            v-else-if="job.state === 'success'"
            class="w-4 h-4 text-yellow-500 flex-shrink-0 mt-0.5"
          />
          <AlertTriangle
            v-else
            class="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5"
          />

          <!-- Contenido -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="font-medium text-gray-800 truncate max-w-xs">{{ job.filename }}</span>
              <span
                v-if="job.result?.publication.quartile_snapshot"
                class="inline-flex px-1.5 py-0.5 rounded-full text-xs font-semibold"
                :class="QUARTILE_COLORS[job.result.publication.quartile_snapshot] ?? 'bg-gray-100 text-gray-600'"
              >
                {{ job.result.publication.quartile_snapshot }}
              </span>
              <span
                v-if="job.result?.publication.is_top10"
                class="inline-flex px-1.5 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-700"
              >
                ★ Top 10%
              </span>
            </div>

            <p v-if="job.state === 'uploading'" class="text-xs text-blue-600 mt-0.5">
              Procesando...
            </p>
            <p v-else-if="job.result" class="text-xs text-gray-500 mt-0.5">
              {{ job.result.message }}
            </p>
            <p v-else-if="job.error" class="text-xs text-red-600 mt-0.5">{{ job.error }}</p>

            <!-- Auditoría: DOI encontrado pero revista no en JCR -->
            <div
              v-if="job.state === 'success' && job.result?.doi_found && !job.result?.journal_found"
              class="mt-2 space-y-1.5"
            >
              <p class="text-xs text-indigo-700 font-medium">Revista no encontrada en la base JCR local</p>
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-xs font-mono bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded truncate max-w-xs">
                  {{ job.result.doi }}
                </span>
                <button
                  class="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                  @click="copyDoi(job.result.doi!)"
                >
                  <Copy class="w-3 h-3" />
                  Copiar DOI
                </button>
                <a
                  :href="`https://doi.org/${job.result.doi}`"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                >
                  <ExternalLink class="w-3 h-3" />
                  Abrir en CrossRef
                </a>
              </div>
              <p class="text-xs text-indigo-400">
                Posibles causas: revista no indexada en JCR, ISSN no coincide, o fuera del período cubierto.
              </p>
            </div>

            <!-- Input DOI manual si no se encontró DOI -->
            <div
              v-if="job.state === 'success' && !job.result?.doi_found"
              class="mt-2 flex items-center gap-2"
            >
              <input
                v-model="job.manualDoi"
                type="text"
                placeholder="Ingresa el DOI manualmente: 10.xxxx/..."
                class="flex-1 px-2 py-1 text-xs border border-yellow-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-yellow-400 font-mono bg-white"
                @keyup.enter="enrichJob(job)"
              />
              <button
                class="px-3 py-1 bg-yellow-500 text-white text-xs font-medium rounded-lg hover:bg-yellow-600 disabled:opacity-50 transition-colors flex items-center gap-1"
                :disabled="job.enriching || !job.manualDoi.trim()"
                @click="enrichJob(job)"
              >
                <Loader2 v-if="job.enriching" class="w-3 h-3 animate-spin" />
                Aplicar
              </button>
            </div>

            <!-- Error del enriquecimiento -->
            <p v-if="job.error && job.state === 'success'" class="text-xs text-red-500 mt-1">
              {{ job.error }}
            </p>
          </div>

          <!-- Botón cerrar -->
          <button
            v-if="job.state !== 'uploading'"
            class="text-gray-400 hover:text-gray-600 flex-shrink-0"
            @click="dismissJob(job.id)"
          >
            <X class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Loader2, CheckCircle, AlertTriangle, X, Search, Copy, ExternalLink } from 'lucide-vue-next'
import type { UploadJob, UploadResult } from '@/types/publication'
import { QUARTILE_COLORS } from '@/types/publication'
import { publicationsApi } from '@/services/api'
import DropZone from '@/components/DropZone.vue'

const jobs = ref<UploadJob[]>([])
const dismissTimers = new Map<string, ReturnType<typeof setTimeout>>()

function scheduleDismiss(id: string, delayMs: number): void {
  const timer = setTimeout(() => dismissJob(id), delayMs)
  dismissTimers.set(id, timer)
}

function onFilesSelected(files: File[]): void {
  files.forEach((file) => startUpload(file))
}

async function startUpload(file: File, manualDoi?: string): Promise<void> {
  const jobId = `${Date.now()}-${Math.random()}`
  const job: UploadJob = {
    id: String(jobId),
    filename: file.name,
    state: 'uploading',
    result: null,
    error: null,
    manualDoi: '',
    enriching: false,
  }
  ;(jobs.value as UploadJob[]).unshift(job)

  try {
    const result = await publicationsApi.uploadPdf(file, manualDoi)
    updateJob(jobId, { state: 'success', result })
    if (result.journal_found) scheduleDismiss(String(jobId), 4000)
  } catch (err: unknown) {
    const detail =
      (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      ?? 'Error al procesar el archivo'
    updateJob(jobId, { state: 'error', error: detail })
    scheduleDismiss(String(jobId), 5000)
  }
}

function updateJob(id: string, patch: Partial<UploadJob>): void {
  const idx = jobs.value.findIndex((j) => j.id === id)
  if (idx !== -1) jobs.value[idx] = { ...jobs.value[idx], ...patch } as UploadJob
}

function dismissJob(id: string): void {
  const timer = dismissTimers.get(id)
  if (timer !== undefined) {
    clearTimeout(timer)
    dismissTimers.delete(id)
  }
  jobs.value = jobs.value.filter((j) => j.id !== id)
}

async function copyDoi(doi: string): Promise<void> {
  await navigator.clipboard.writeText(doi)
}

async function enrichJob(job: UploadJob): Promise<void> {
  if (!job.result?.publication.id || !job.manualDoi.trim()) return
  updateJob(job.id, { enriching: true })
  try {
    const updated: UploadResult = await publicationsApi.enrichWithDoi(
      job.result.publication.id,
      job.manualDoi.trim(),
    )
    updateJob(job.id, { result: updated, enriching: false })
    // Si ahora encuentra la revista, programar auto-dismiss
    if (updated.journal_found) scheduleDismiss(job.id, 4000)
  } catch (err: unknown) {
    const detail =
      (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      ?? 'No se pudo enriquecer con ese DOI'
    updateJob(job.id, { error: detail, enriching: false })
  }
}
</script>
