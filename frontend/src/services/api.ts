import axios from 'axios'
import type { UploadResult } from '@/types/publication'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api',
  timeout: 30_000,
})

export const publicationsApi = {
  uploadPdf: async (file: File): Promise<UploadResult> => {
    const form = new FormData()
    form.append('file', file)

    const { data } = await api.post<UploadResult>('/publications/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },
}

export default api
