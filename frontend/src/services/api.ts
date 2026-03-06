import axios from 'axios'
import type {
  Publication,
  UploadResult,
  JournalListResponse,
  Researcher,
  Student,
  ScientificProject,
  PaginatedResponse,
  ProjectActivity,
  ResponsibilityAssignment,
  MyTask,
  AcademicMember,
} from '@/types/publication'

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

export const researchersApi = {
  search: async (params: {
    q?: string
    member_type?: string
    is_active?: boolean
    page?: number
    limit?: number
  }): Promise<PaginatedResponse<Researcher>> => {
    const p: Record<string, string | number | boolean> = {}
    if (params.q) p.q = params.q
    if (params.member_type) p.member_type = params.member_type
    if (params.is_active !== undefined) p.is_active = params.is_active
    if (params.page) p.page = params.page
    if (params.limit) p.limit = params.limit
    const { data } = await api.get<PaginatedResponse<Researcher>>('/researchers', { params: p })
    return data
  },
}

export const studentsApi = {
  search: async (params: {
    q?: string
    status?: string
    program?: string
    page?: number
    limit?: number
  }): Promise<PaginatedResponse<Student>> => {
    const p: Record<string, string | number> = {}
    if (params.q) p.q = params.q
    if (params.status) p.status = params.status
    if (params.program) p.program = params.program
    if (params.page) p.page = params.page
    if (params.limit) p.limit = params.limit
    const { data } = await api.get<PaginatedResponse<Student>>('/students', { params: p })
    return data
  },
}

export const projectsApi = {
  search: async (params: {
    q?: string
    status?: string
    grant_type?: string
    page?: number
    limit?: number
  }): Promise<PaginatedResponse<ScientificProject>> => {
    const p: Record<string, string | number> = {}
    if (params.q) p.q = params.q
    if (params.status) p.status = params.status
    if (params.grant_type) p.grant_type = params.grant_type
    if (params.page) p.page = params.page
    if (params.limit) p.limit = params.limit
    const { data } = await api.get<PaginatedResponse<ScientificProject>>('/projects', { params: p })
    return data
  },
}

export const projectActivitiesApi = {
  list: async (projectId: number): Promise<ProjectActivity[]> => {
    const { data } = await api.get<ProjectActivity[]>('/project-activities', {
      params: { project_id: projectId },
    })
    return data
  },

  create: async (payload: {
    project_id: number
    description: string
    number?: number | null
    start_month?: number
    end_month?: number
    status?: string
    progress?: number
    budget_allocated?: number | null
    notes?: string | null
    sort_order?: number
  }): Promise<ProjectActivity> => {
    const { data } = await api.post<ProjectActivity>('/project-activities', payload)
    return data
  },

  update: async (id: number, payload: Partial<{
    description: string
    number: number | null
    start_month: number
    end_month: number
    status: string
    progress: number
    budget_allocated: number | null
    notes: string | null
    sort_order: number
  }>): Promise<ProjectActivity> => {
    const { data } = await api.put<ProjectActivity>(`/project-activities/${id}`, payload)
    return data
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/project-activities/${id}`)
  },
}

export const responsibilitiesApi = {
  list: async (resourceType: string, resourceId: number): Promise<ResponsibilityAssignment[]> => {
    const { data } = await api.get<ResponsibilityAssignment[]>('/responsibilities', {
      params: { resource_type: resourceType, resource_id: resourceId },
    })
    return data
  },

  create: async (payload: {
    resource_type: string
    resource_id: number
    raci_role: string
    member_id?: number | null
  }): Promise<ResponsibilityAssignment> => {
    const { data } = await api.post<ResponsibilityAssignment>('/responsibilities', payload)
    return data
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/responsibilities/${id}`)
  },

  myTasks: async (memberId?: number): Promise<MyTask[]> => {
    const params: Record<string, number> = {}
    if (memberId !== undefined) params.member_id = memberId
    const { data } = await api.get<MyTask[]>('/my-tasks', { params })
    return data
  },

  myTasksMembers: async (): Promise<AcademicMember[]> => {
    const { data } = await api.get<AcademicMember[]>('/my-tasks/members')
    return data
  },
}

export default api
