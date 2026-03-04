import { ref } from 'vue'
import type { UploadResult } from '@/types/publication'
import { publicationsApi } from '@/services/api'

type UploadState = 'idle' | 'uploading' | 'success' | 'error'

export function useUploadPdf() {
  const state = ref<UploadState>('idle')
  const result = ref<UploadResult | null>(null)
  const error = ref<string | null>(null)
  const progress = ref(0)

  async function upload(file: File): Promise<void> {
    state.value = 'uploading'
    result.value = null
    error.value = null
    progress.value = 0

    try {
      result.value = await publicationsApi.uploadPdf(file)
      state.value = 'success'
      progress.value = 100
    } catch (err: unknown) {
      state.value = 'error'
      error.value = extractErrorMessage(err)
    }
  }

  function reset(): void {
    state.value = 'idle'
    result.value = null
    error.value = null
    progress.value = 0
  }

  return { state, result, error, progress, upload, reset }
}

function extractErrorMessage(err: unknown): string {
  if (err instanceof Error) return err.message
  if (typeof err === 'object' && err !== null) {
    const detail = (err as Record<string, unknown>)?.detail
    if (typeof detail === 'string') return detail
  }
  return 'Error desconocido al procesar el archivo'
}
