<script setup lang="ts">
import { ref, computed } from 'vue'
import { X, Hash, Loader2, CheckCircle, AlertTriangle } from 'lucide-vue-next'
import { publicationsApi } from '@/services/api'
import type { UploadResult } from '@/types/publication'
import { QUARTILE_COLORS } from '@/types/publication'

const emit = defineEmits<{
  close: []
  done: [result: UploadResult]
}>()

const doi = ref('')
const state = ref<'idle' | 'loading' | 'success' | 'error'>('idle')
const result = ref<UploadResult | null>(null)
const errorMsg = ref('')

const DOI_RE = /^10\.\d{4,9}\/[-._;()/:a-zA-Z0-9]+$/

const isValidDoi = computed(() => DOI_RE.test(doi.value.trim().replace(/^https?:\/\/(dx\.)?doi\.org\//i, '')))

function normalizeDoi(raw: string): string {
  return raw.trim().replace(/^https?:\/\/(dx\.)?doi\.org\//i, '')
}

async function submit(): Promise<void> {
  if (!isValidDoi.value) return
  state.value = 'loading'
  errorMsg.value = ''
  result.value = null

  try {
    const r = await publicationsApi.uploadWithDoi(normalizeDoi(doi.value))
    result.value = r
    state.value = 'success'
    emit('done', r)
  } catch (err: unknown) {
    state.value = 'error'
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    errorMsg.value = detail ?? 'No se pudo procesar el DOI'
  }
}

function handleClose(): void {
  if (state.value === 'success') {
    emit('close')
  } else {
    emit('close')
  }
}
</script>

<template>
  <!-- Backdrop -->
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
    @click.self="handleClose"
  >
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 overflow-hidden">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
        <div class="flex items-center gap-2">
          <Hash class="w-5 h-5 text-blue-600" />
          <h2 class="text-base font-semibold text-gray-900">Ingresar DOI manualmente</h2>
        </div>
        <button
          class="text-gray-400 hover:text-gray-600 transition-colors"
          @click="handleClose"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Body -->
      <div class="px-6 py-5">
        <!-- Idle / Error state: show input -->
        <template v-if="state !== 'success'">
          <p class="text-sm text-gray-500 mb-4">
            Útil cuando el PDF no contiene DOI legible. Se consultará OpenAlex con el DOI
            para obtener los datos de la revista.
          </p>

          <label class="block text-sm font-medium text-gray-700 mb-1">DOI</label>
          <input
            v-model="doi"
            type="text"
            placeholder="Ej: 10.1016/j.example.2023.01.001"
            class="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
            :class="
              doi && !isValidDoi
                ? 'border-red-300 focus:ring-red-400'
                : 'border-gray-200'
            "
            :disabled="state === 'loading'"
            @keyup.enter="submit"
          />
          <p v-if="doi && !isValidDoi" class="text-xs text-red-500 mt-1">
            Formato inválido. Debe comenzar con 10.xxxx/
          </p>

          <p v-if="state === 'error'" class="mt-3 text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">
            {{ errorMsg }}
          </p>
        </template>

        <!-- Success state -->
        <template v-else-if="result">
          <div
            class="flex items-start gap-3 p-3 rounded-lg"
            :class="result.journal_found ? 'bg-green-50' : 'bg-yellow-50'"
          >
            <CheckCircle
              v-if="result.journal_found"
              class="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5"
            />
            <AlertTriangle v-else class="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
            <div class="min-w-0">
              <p class="text-sm font-medium text-gray-800">{{ result.message }}</p>
              <p v-if="result.publication.title" class="text-xs text-gray-500 mt-0.5 truncate">
                {{ result.publication.title }}
              </p>
            </div>
          </div>

          <!-- Métricas si encontró journal -->
          <div v-if="result.journal_found && result.journal" class="mt-4 grid grid-cols-3 gap-3">
            <div class="bg-gray-50 rounded-lg p-3 text-center">
              <p class="text-xs text-gray-400 mb-1">IF</p>
              <p class="font-bold text-gray-800">
                {{ result.journal.impact_factor?.toFixed(3) ?? '—' }}
              </p>
            </div>
            <div class="bg-gray-50 rounded-lg p-3 text-center">
              <p class="text-xs text-gray-400 mb-1">Cuartil</p>
              <span
                v-if="result.publication.quartile_snapshot"
                class="inline-flex px-2 py-0.5 rounded-full text-xs font-semibold"
                :class="QUARTILE_COLORS[result.publication.quartile_snapshot] ?? 'bg-gray-100 text-gray-600'"
              >
                {{ result.publication.quartile_snapshot }}
              </span>
              <span v-else class="text-gray-400">—</span>
            </div>
            <div class="bg-gray-50 rounded-lg p-3 text-center">
              <p class="text-xs text-gray-400 mb-1">JIF %</p>
              <p class="font-bold text-gray-800">
                {{ result.publication.jif_percentile_snapshot?.toFixed(1) ?? '—' }}
              </p>
            </div>
          </div>
        </template>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 bg-gray-50 border-t border-gray-100 flex justify-end gap-3">
        <button
          class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors"
          @click="handleClose"
        >
          {{ state === 'success' ? 'Cerrar' : 'Cancelar' }}
        </button>
        <button
          v-if="state !== 'success'"
          class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          :disabled="!isValidDoi || state === 'loading'"
          @click="submit"
        >
          <Loader2 v-if="state === 'loading'" class="w-4 h-4 animate-spin" />
          {{ state === 'loading' ? 'Buscando...' : 'Buscar y registrar' }}
        </button>
      </div>
    </div>
  </div>
</template>
