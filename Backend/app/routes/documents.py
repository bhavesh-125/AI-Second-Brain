# backend/app/routes/documents.py  — full updated file

from dbm import error

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.models.user import User
from app.schemas.document import DocumentResponse, DocumentListResponse
from app.schemas.chunk import ChunkResponse, ChunkListResponse
from app.services.file_service import validate_file, save_upload_file, delete_file_from_disk
from app.services.extraction_service import extract_text_from_file, split_text_into_chunks
from app.services.embedding_service import embed_chunks_for_document
from app.core.security import get_current_user

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Step 1: validate file type
    validate_file(file)

    # Step 2: save to disk
    file_data = await save_upload_file(file)

    # Step 3: save metadata to DB
    document = Document(
        filename=file.filename,
        stored_filename=file_data["stored_filename"],
        file_path=file_data["file_path"],
        file_type=file.content_type,
        file_size=file_data["file_size"],
        user_id=current_user.id
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Step 4: extract text and create chunks
    # We wrap this in a try/except so a bad PDF doesn't kill the upload.
    # The document row is already saved — we just won't have chunks if this fails.
    try:
        raw_text = extract_text_from_file(document.file_path, document.file_type)
        text_chunks = split_text_into_chunks(raw_text)

        # Build all chunk objects and bulk-insert them
        chunk_objects = [
            DocumentChunk(
                document_id=document.id,
                user_id=current_user.id,
                content=chunk_text,
                chunk_index=index,
                chunk_size=len(chunk_text)
            )
            for index, chunk_text in enumerate(text_chunks)
        ]

        if chunk_objects:
            db.add_all(chunk_objects)   # bulk insert — much faster than adding one by one
            db.commit()


 # Create embeddings for saved chunks
        embedded_count = embed_chunks_for_document(document.id, db)

        print(f"Embedded {embedded_count} chunks for document {document.id}")

    except Exception as error:
        print(f"Document processing failed for document {document.id}: {error}")

    return document


@router.get("/", response_model=DocumentListResponse)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    documents = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return {"total": len(documents), "documents": documents}


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if document.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return document


@router.get("/{document_id}/chunks", response_model=ChunkListResponse)
def get_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns all text chunks for a given document.
    This is the endpoint the RAG system will query later.
    """
    # First verify the document exists and belongs to this user
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if document.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Fetch chunks in order
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )

    return {"total": len(chunks), "chunks": chunks}


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if document.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Chunks are auto-deleted by CASCADE (and the relationship cascade="all, delete-orphan")
    delete_file_from_disk(document.file_path)
    db.delete(document)
    db.commit()
