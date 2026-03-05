import axios from 'axios'
import type { Publication, UploadResult } from '@/types/publication'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api',
  timeout: 30_000,
})

export const publicationsApi = {
  getAll: async (): Promise<Publication[]> => {
    const { data } = await api.get<Publication[]>('/publications')
    return data
  },

  uploadPdf: async (file: File, manualDoi?: string): Promise<UploadResult> => {
    const form = new FormData()
    form.append('file', file)
    if (manualDoi) form.append('doi', manualDoi)

    const { data } = await api.post<UploadResult>('/publications/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  uploadWithDoi: async (doi: string): Promise<UploadResult> => {
    const form = new FormData()
    form.append('doi', doi)

    const { data } = await api.post<UploadResult>('/publications/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  enrichWithDoi: async (publicationId: number, doi: string): Promise<UploadResult> => {
    const form = new FormData()
    form.append('doi', doi)

    const { data } = await api.post<UploadResult>(
      `/publications/${publicationId}/enrich-doi`,
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
    return data
  },
}

export default api
