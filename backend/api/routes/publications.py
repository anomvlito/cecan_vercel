"""Endpoint principal: upload de PDF con extracción de DOI y métricas JCR."""
import json
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from database.session import get_db
from core.models import Publication
from core.schemas import JournalRead, UploadResult, PublicationRead
from services.doi_extractor import extract_doi_from_pdf_bytes
from services.openalex_service import fetch_work_by_doi
from services.journal_service import (
    find_journal_by_issn,
    find_journal_by_title,
    find_journal_by_title_and_publisher,
    derive_quartile,
    derive_percentile,
)

router = APIRouter(prefix="/publications", tags=["publications"])

MAX_PDF_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/upload", response_model=UploadResult, status_code=status.HTTP_201_CREATED)
async def upload_pdf(
    file: Optional[UploadFile] = File(None),
    doi: Optional[str] = Form(None),
    db: Session = Depends(get_db),
) -> UploadResult:
    """Sube un PDF y/o ingresa un DOI manual para obtener métricas JCR.

    Modos de uso:
    - file + sin doi    → extrae DOI del PDF automáticamente
    - file + doi        → usa el DOI provisto, ignora extracción
    - sin file + doi    → crea entrada solo con metadatos por DOI
    """
    if file is None and not doi:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere un archivo PDF o un DOI",
        )

    filename: Optional[str] = None
    extracted_doi: Optional[str] = None
    doi_method: Optional[str] = None

    if file is not None:
        _validate_pdf(file)
        pdf_bytes = await file.read()
        if len(pdf_bytes) > MAX_PDF_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="El archivo PDF supera el límite de 50 MB",
            )
        filename = file.filename

        if doi:
            # DOI provisto manualmente: no extraer del PDF
            extracted_doi = doi.strip()
            doi_method = "manual"
        else:
            extracted_doi, doi_method = extract_doi_from_pdf_bytes(pdf_bytes)
    else:
        # Solo DOI, sin archivo
        extracted_doi = doi.strip()
        doi_method = "manual"

    # Verificar duplicado por DOI
    if extracted_doi:
        existing = db.query(Publication).filter(Publication.doi == extracted_doi).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe una publicación con el DOI {extracted_doi} (id={existing.id})",
            )

    # Verificar duplicado por filename
    if filename:
        existing_by_file = db.query(Publication).filter(
            Publication.pdf_filename == filename
        ).first()
        if existing_by_file:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe una publicación con el archivo '{filename}' (id={existing_by_file.id})",
            )

    pub = Publication(
        pdf_filename=filename,
        status="uploaded",
        doi_extraction_method=doi_method if extracted_doi else "not_found",
    )

    work_meta = None
    journal = None

    if extracted_doi:
        pub.doi = extracted_doi
        pub.status = "doi_extracted"

        work_meta = await fetch_work_by_doi(extracted_doi)

        if work_meta:
            pub.title = work_meta.title
            pub.year = work_meta.year
            pub.volume = work_meta.volume
            pub.issue = work_meta.issue
            pub.pages = work_meta.pages
            pub.openalex_data = json.dumps(work_meta.raw)
            pub.journal_issn_raw = work_meta.issn

            for issn in work_meta.issn_list:
                journal = find_journal_by_issn(db, issn)
                if journal:
                    break

            if not journal and work_meta.journal_name and work_meta.publisher:
                journal = find_journal_by_title_and_publisher(
                    db, work_meta.journal_name, work_meta.publisher
                )

            if not journal and work_meta.journal_name:
                journal = find_journal_by_title(db, work_meta.journal_name)

            if journal:
                pub.journal_id = journal.id
                pub.impact_factor_snapshot = journal.impact_factor
                pub.quartile_snapshot = derive_quartile(journal)
                pub.jif_percentile_snapshot = derive_percentile(journal)
                pub.status = "enriched"

    try:
        db.add(pub)
        db.commit()
        db.refresh(pub)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una publicación con el DOI {extracted_doi}",
        )

    journal_read = JournalRead.model_validate(journal) if journal else None

    return UploadResult(
        publication=PublicationRead.model_validate(pub),
        doi_found=bool(extracted_doi),
        doi=extracted_doi,
        doi_method=doi_method if extracted_doi else None,
        journal_found=bool(journal),
        journal=journal_read,
        message=_build_message(extracted_doi, journal),
    )


@router.post("/{publication_id}/enrich-doi", response_model=UploadResult)
async def enrich_with_doi(
    publication_id: int,
    doi: str = Form(...),
    db: Session = Depends(get_db),
) -> UploadResult:
    """Enriquece una publicación existente usando un DOI ingresado manualmente."""
    pub = (
        db.query(Publication)
        .options(joinedload(Publication.journal))
        .filter(Publication.id == publication_id)
        .first()
    )
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")

    doi = doi.strip()

    # Verificar que el DOI no pertenezca a otra publicación
    conflict = (
        db.query(Publication)
        .filter(Publication.doi == doi, Publication.id != publication_id)
        .first()
    )
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El DOI {doi} ya está registrado en la publicación {conflict.id}",
        )

    pub.doi = doi
    pub.doi_extraction_method = "manual"
    pub.status = "doi_extracted"

    work_meta = await fetch_work_by_doi(doi)
    journal = None

    if work_meta:
        pub.title = pub.title or work_meta.title
        pub.year = pub.year or work_meta.year
        pub.volume = work_meta.volume
        pub.issue = work_meta.issue
        pub.pages = work_meta.pages
        pub.openalex_data = json.dumps(work_meta.raw)
        pub.journal_issn_raw = work_meta.issn

        for issn in work_meta.issn_list:
            journal = find_journal_by_issn(db, issn)
            if journal:
                break

        if not journal and work_meta.journal_name and work_meta.publisher:
            journal = find_journal_by_title_and_publisher(
                db, work_meta.journal_name, work_meta.publisher
            )

        if not journal and work_meta.journal_name:
            journal = find_journal_by_title(db, work_meta.journal_name)

        if journal:
            pub.journal_id = journal.id
            pub.impact_factor_snapshot = journal.impact_factor
            pub.quartile_snapshot = derive_quartile(journal)
            pub.jif_percentile_snapshot = derive_percentile(journal)
            pub.status = "enriched"

    try:
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
        doi_found=True,
        doi=doi,
        doi_method="manual",
        journal_found=bool(journal),
        journal=journal_read,
        message=_build_message(doi, journal),
    )


@router.delete("/{publication_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_publication(
    publication_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Elimina una publicación por ID."""
    pub = db.query(Publication).filter(Publication.id == publication_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
    db.delete(pub)
    db.commit()


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
    pub = (
        db.query(Publication)
        .options(joinedload(Publication.journal))
        .filter(Publication.id == publication_id)
        .first()
    )
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
        return "PDF subido. No se encontró DOI en el documento."
    if not journal:
        return f"DOI encontrado ({doi}). No se encontró la revista en la base de datos JCR."
    q = derive_quartile(journal) or "?"
    return f"Revista vinculada exitosamente. {q}, IF: {journal.impact_factor}"
