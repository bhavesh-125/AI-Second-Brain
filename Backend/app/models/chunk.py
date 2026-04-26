from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from pgvector.sqlalchemy import Vector

from app.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    # Unique ID for each chunk
    id = Column(Integer, primary_key=True, index=True)

    # Which document this chunk belongs to
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)

    # Which user owns this chunk
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Actual text content of the chunk
    content = Column(Text, nullable=False)

    # Position/order of chunk in original document
    chunk_index = Column(Integer, nullable=False)

    # Size of chunk in characters
    chunk_size = Column(Integer, nullable=False)

    # BAAI/bge-base-en-v1.5 creates 768-dimensional vectors
    embedding = Column(Vector(768), nullable=True)

    # Chunk creation time
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to document
    document = relationship("Document", back_populates="chunks")
