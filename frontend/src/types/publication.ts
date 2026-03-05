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

export const QUARTILE_COLORS: Record<string, string> = {
  Q1: 'bg-green-100 text-green-800',
  Q2: 'bg-blue-100 text-blue-800',
  Q3: 'bg-yellow-100 text-yellow-800',
  Q4: 'bg-red-100 text-red-800',
}
