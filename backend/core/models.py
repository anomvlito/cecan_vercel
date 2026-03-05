from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Journal(Base):
    """Datos JCR de revistas científicas (importados desde Excel JCR)."""

    __tablename__ = "journals"

    id = Column(Integer, primary_key=True)
    issn = Column(String(10), index=True, nullable=True)
    eissn = Column(String(10), index=True, nullable=True)
    title = Column(String(500), nullable=False)
    title_abbrev = Column(String(200), nullable=True)
    iso_abbrev = Column(String(200), nullable=True)
    year = Column(Integer, nullable=True)

    # Métricas de impacto
    impact_factor = Column(Float, nullable=True)
    impact_factor_5yr = Column(Float, nullable=True)
    eigenfactor = Column(Float, nullable=True)
    article_influence = Column(Float, nullable=True)
    immediacy_index = Column(Float, nullable=True)
    norm_eigenfactor = Column(Float, nullable=True)

    # Rankings
    quartile_rank = Column(String(20), nullable=True)   # Q1, Q2, Q3, Q4 o ranking "10/100"
    jif_percentile = Column(Float, nullable=True)
    category_ranking = Column(String(100), nullable=True)  # e.g. "15/250"
    categories_code = Column(String(200), nullable=True)
    categories_description = Column(Text, nullable=True)
    edition = Column(String(20), nullable=True)  # SCIE, SSCI, ESCI, etc.

    # Editorial info
    publisher_name = Column(String(500), nullable=True)
    country = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)

    # Citas
    total_cites = Column(Integer, nullable=True)
    cited_half_life = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    publications = relationship("Publication", back_populates="journal")


class Publication(Base):
    """Publicación científica subida por un usuario."""

    __tablename__ = "publications"

    id = Column(Integer, primary_key=True)
    title = Column(String(1000), nullable=True)
    doi = Column(String(300), unique=True, nullable=True)
    abstract = Column(Text, nullable=True)
    year = Column(Integer, nullable=True)
    volume = Column(String(50), nullable=True)
    issue = Column(String(50), nullable=True)
    pages = Column(String(100), nullable=True)

    # Archivo PDF
    pdf_filename = Column(String(500), nullable=True)
    pdf_storage_path = Column(String(1000), nullable=True)  # Supabase Storage path

    # Revista vinculada
    journal_id = Column(Integer, ForeignKey("journals.id"), nullable=True)
    journal_issn_raw = Column(String(10), nullable=True)  # ISSN detectado antes de vincular

    # Métricas en el momento de la publicación (snapshot)
    impact_factor_snapshot = Column(Float, nullable=True)
    quartile_snapshot = Column(String(5), nullable=True)
    jif_percentile_snapshot = Column(Float, nullable=True)

    # Estado de procesamiento
    status = Column(String(50), default="uploaded")
    # uploaded → doi_extracted → enriched → complete | failed

    doi_extraction_method = Column(String(50), nullable=True)  # pdf_text, metadata, manual
    openalex_data = Column(Text, nullable=True)  # JSON raw de OpenAlex

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    journal = relationship("Journal", back_populates="publications")
