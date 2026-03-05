from typing import Optional
from pydantic import BaseModel, ConfigDict, computed_field


class JournalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    issn: Optional[str] = None
    eissn: Optional[str] = None
    title: str
    title_abbrev: Optional[str] = None
    year: Optional[int] = None
    impact_factor: Optional[float] = None
    impact_factor_5yr: Optional[float] = None
    quartile_rank: Optional[str] = None
    jif_percentile: Optional[float] = None
    categories_description: Optional[str] = None
    publisher_name: Optional[str] = None
    country: Optional[str] = None
    eigenfactor: Optional[float] = None
    article_influence: Optional[float] = None


class PublicationCreate(BaseModel):
    doi: Optional[str] = None
    title: Optional[str] = None
    year: Optional[int] = None
    pdf_filename: Optional[str] = None
    pdf_storage_path: Optional[str] = None


class PublicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: Optional[str] = None
    doi: Optional[str] = None
    year: Optional[int] = None
    pdf_filename: Optional[str] = None
    status: str
    journal_id: Optional[int] = None
    impact_factor_snapshot: Optional[float] = None
    quartile_snapshot: Optional[str] = None
    jif_percentile_snapshot: Optional[float] = None
    journal: Optional[JournalRead] = None

    @computed_field
    @property
    def is_top10(self) -> bool:
        """True si la revista está en el top 10% (JIF percentile ≥ 90)."""
        return self.jif_percentile_snapshot is not None and self.jif_percentile_snapshot >= 90.0


class JournalListResponse(BaseModel):
    """Respuesta paginada para el listado de revistas."""
    items: list[JournalRead]
    total: int
    page: int
    limit: int
    pages: int


class UploadResult(BaseModel):
    """Resultado del proceso completo de upload + enrichment."""
    publication: PublicationRead
    doi_found: bool
    doi: Optional[str] = None
    doi_method: Optional[str] = None
    journal_found: bool
    journal: Optional[JournalRead] = None
    message: str
