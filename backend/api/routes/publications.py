"""Endpoint principal: upload de PDF con extracción de DOI y métricas JCR."""
import json
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm import joinedload

from database.session import get_db
from core.models import Publication
from core.schemas import JournalRead, UploadResult, PublicationRead
from services.doi_extractor import extract_doi_from_pdf_bytes
from services.openalex_service import fetch_work_by_doi
from services.journal_service import find_journal_by_issn, find_journal_by_title

router = APIRouter(prefix="/publications", tags=["publications"])

MAX_PDF_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/upload", response_model=UploadResult, status_code=status.HTTP_201_CREATED)
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> UploadResult:
    """Sube un PDF, extrae DOI, consulta OpenAlex y vincula métricas JCR.

    Flujo:
    1. Validar archivo PDF
    2. Extraer DOI del texto
    3. Consultar OpenAlex para obtener ISSN y metadatos
    4. Buscar revista en BD JCR por ISSN (todos los ISSNs disponibles)
    5. Guardar publicación con métricas

    Returns:
        UploadResult con publicación guardada y journal vinculado
    """
    _validate_pdf(file)

    pdf_bytes = await file.read()
    if len(pdf_bytes) > MAX_PDF_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El archivo PDF supera el límite de 50 MB",
        )

    doi, doi_method = extract_doi_from_pdf_bytes(pdf_bytes)

    # Verificar DOI duplicado antes de procesar
    if doi:
        existing = db.query(Publication).filter(Publication.doi == doi).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe una publicación con el DOI {doi} (id={existing.id})",
            )

    pub = Publication(
        pdf_filename=file.filename,
        status="uploaded",
        doi_extraction_method=doi_method if doi else "not_found",
    )

    work_meta = None
    journal = None

    if doi:
        pub.doi = doi
        pub.status = "doi_extracted"

        work_meta = await fetch_work_by_doi(doi)

        if work_meta:
            pub.title = work_meta.title
            pub.year = work_meta.year
            pub.volume = work_meta.volume
            pub.issue = work_meta.issue
            pub.pages = work_meta.pages
            pub.openalex_data = json.dumps(work_meta.raw)
            pub.journal_issn_raw = work_meta.issn

            # Buscar journal usando todos los ISSNs disponibles de OpenAlex
            for issn in work_meta.issn_list:
                journal = find_journal_by_issn(db, issn)
                if journal:
                    break

            # Fallback por nombre de revista
            if not journal and work_meta.journal_name:
                journal = find_journal_by_title(db, work_meta.journal_name)

            if journal:
                pub.journal_id = journal.id
                pub.impact_factor_snapshot = journal.impact_factor
                pub.quartile_snapshot = journal.quartile_rank
                pub.jif_percentile_snapshot = journal.jif_percentile
                pub.status = "enriched"

    try:
        db.add(pub)
        db.commit()
        db.refresh(pub)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una publicación con el DOI {doi}",
        )

    journal_read = JournalRead.model_validate(journal) if journal else None

    return UploadResult(
        publication=PublicationRead.model_validate(pub),
        doi_found=bool(doi),
        doi=doi,
        doi_method=doi_method if doi else None,
        journal_found=bool(journal),
        journal=journal_read,
        message=_build_message(doi, journal),
    )


@router.get("", response_model=list[PublicationRead])
def list_publications(db: Session = Depends(get_db)) -> list[Publication]:
    """Lista todas las publicaciones ordenadas por fecha de creación."""
    return (
        db.query(Publication)
        .options(joinedload(Publication.journal))
        .order_by(Publication.created_at.desc())
        .all()
    )


@router.get("/{publication_id}", response_model=PublicationRead)
def get_publication(publication_id: int, db: Session = Depends(get_db)) -> Publication:
    pub = db.query(Publication).filter(Publication.id == publication_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
    return pub


def _validate_pdf(file: UploadFile) -> None:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se aceptan archivos PDF",
        )
    if file.content_type and file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content-type inválido: {file.content_type}",
        )


def _build_message(doi: Optional[str], journal) -> str:
    if not doi:
        return "PDF subido correctamente. No se encontró DOI en el documento."
    if not journal:
        return f"DOI encontrado ({doi}). No se encontró la revista en la base de datos JCR."
    return f"DOI encontrado y revista vinculada exitosamente. {journal.quartile_rank}, IF: {journal.impact_factor}"
