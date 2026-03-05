import axios from 'axios'
import type { Publication, UploadResult, JournalListResponse } from '@/types/publication'

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

  delete: async (publicationId: number): Promise<void> => {
    await api.delete(`/publications/${publicationId}`)
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

export const journalsApi = {
  search: async (params: {
    q?: string
    quartile?: string
    min_percentile?: number | null
    max_percentile?: number | null
    page?: number
    limit?: number
  }): Promise<JournalListResponse> => {
    const p: Record<string, string | number> = {}
    if (params.q) p.q = params.q
    if (params.quartile) p.quartile = params.quartile
    if (params.min_percentile != null) p.min_percentile = params.min_percentile
    if (params.max_percentile != null) p.max_percentile = params.max_percentile
    if (params.page) p.page = params.page
    if (params.limit) p.limit = params.limit
    const { data } = await api.get<JournalListResponse>('/journals', { params: p })
    return data
  },
}

export default api
