export interface Journal {
  id: number
  issn: string | null
  eissn: string | null
  title: string
  title_abbrev: string | null
  year: number | null
  impact_factor: number | null
  impact_factor_5yr: number | null
  quartile_rank: string | null
  jif_percentile: number | null
  categories_description: string | null
  publisher_name: string | null
  country: string | null
  eigenfactor: number | null
  article_influence: number | null
}

export interface Publication {
  id: number
  title: string | null
  doi: string | null
  year: number | null
  pdf_filename: string | null
  status: PublicationStatus
  journal_id: number | null
  impact_factor_snapshot: number | null
  quartile_snapshot: string | null
  jif_percentile_snapshot: number | null
  is_top10: boolean
  journal_issn_raw: string | null
  journal: Journal | null
}

export type PublicationStatus =
  | 'uploaded'
  | 'doi_extracted'
  | 'enriched'
  | 'complete'
  | 'failed'

export interface UploadResult {
  publication: Publication
  doi_found: boolean
  doi: string | null
  doi_method: string | null
  journal_found: boolean
  journal: Journal | null
  message: string
}

export type QuartileRank = 'Q1' | 'Q2' | 'Q3' | 'Q4'

export interface UploadJob {
  id: string
  filename: string
  state: 'uploading' | 'success' | 'error'
  result: UploadResult | null
  error: string | null
  manualDoi: string
  enriching: boolean
}

export interface JournalListResponse {
  items: Journal[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface Researcher {
  id: number
  full_name: string
  email: string | null
  rut: string | null
  institution: string | null
  member_type: string | null
  wp_id: number | null
  is_active: boolean
  created_at: string | null
  orcid: string | null
  first_name: string | null
  last_name: string | null
  category: string | null
  citaciones_totales: number | null
  indice_h: number | null
  works_count: number | null
  i10_index: number | null
  url_foto: string | null
  start_date: string | null
  end_date: string | null
}

export interface Student {
  id: number
  full_name: string
  email: string | null
  rut: string | null
  university: string | null
  program: string | null
  status: string
  start_date: string | null
  graduation_date: string | null
  tutor_name: string | null
  co_tutor_name: string | null
  wp_id: number | null
  created_at: string | null
  updated_at: string | null
}

export interface ScientificProject {
  id: number
  title: string
  code: string | null
  work_package: string | null
  grant_type: string | null
  pi_id: number | null
  pi_name: string | null
  start_date: string | null
  end_date: string | null
  status: string | null
  progress: number | null
  budget_allocated: number | null
  budget_executed: number | null
  currency: string | null
  years_covered: string | null
  color: string | null
  notes: string | null
  created_at: string | null
  updated_at: string | null
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  pages: number
}

export const QUARTILE_COLORS: Record<string, string> = {
  Q1: 'bg-green-100 text-green-800',
  Q2: 'bg-blue-100 text-blue-800',
  Q3: 'bg-yellow-100 text-yellow-800',
  Q4: 'bg-red-100 text-red-800',
}
