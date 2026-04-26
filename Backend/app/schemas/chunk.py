from datetime import datetime
from pydantic import BaseModel


class ChunkResponse(BaseModel):
    """What we return when someone requests a specific chunk."""
    id: int
    document_id: int
    chunk_index: int
    chunk_size: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChunkListResponse(BaseModel):
    """A list of chunks with a count — returned when listing chunks for a document."""
    total: int
    chunks: list[ChunkResponse]
