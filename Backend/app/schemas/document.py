# backend/app/schemas/document.py

from datetime import datetime
from pydantic import BaseModel  # BaseModel is the base class for all Pydantic schemas


class DocumentResponse(BaseModel):
    """
    This schema defines what the API sends back to the client
    after a successful upload or when fetching a document.

    Notice: file_path is NOT here — that's a server-side detail.
    We never expose where files live on our disk.
    """
    id: int
    filename: str       # the original filename the user uploaded
    file_type: str      # e.g. "application/pdf"
    file_size: int      # size in bytes
    user_id: int        # which user owns this document
    created_at: datetime

    class Config:
        # from_attributes=True allows Pydantic to read data from a SQLAlchemy
        # model object (not just a plain dict). Without this, return document
        # in the route would fail because document is a SQLAlchemy object.
        from_attributes = True


class DocumentListResponse(BaseModel):
    """
    Wraps a list of documents with a total count.
    This makes life easier for the frontend — it knows how many
    results exist without counting the array itself.
    """
    total: int                          # how many documents this user has
    documents: list[DocumentResponse]   # the actual list of documents
