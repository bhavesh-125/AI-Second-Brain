# backend/app/models/document.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base  # Base is the parent class all models inherit from


class Document(Base):
    # This is the actual table name that will be created in PostgreSQL
    __tablename__ = "documents"

    # Primary key — auto-increments with each new row
    id = Column(Integer, primary_key=True, index=True)

    # The original name of the file as the user named it on their computer
    # e.g. "my_python_notes.pdf"
    filename = Column(String, nullable=False)

    # The name WE give the file when saving it to disk — a UUID
    # e.g. "3f2a9c1d-4e5b-6f7a-8b9c-0d1e2f3a4b5c.pdf"
    # unique=True prevents two rows ever pointing to the same disk file
    stored_filename = Column(String, nullable=False, unique=True)

    # The full path on disk where the file is saved
    # e.g. "uploads/3f2a9c1d-4e5b-6f7a-8b9c-0d1e2f3a4b5c.pdf"
    file_path = Column(String, nullable=False)

    # The MIME type of the file — tells us what kind of file it is
    # e.g. "application/pdf" or "text/plain"
    file_type = Column(String, nullable=False)

    # Size of the file in bytes — BigInteger safely handles files larger than 2 GB
    # Regular Integer would overflow on large files
    file_size = Column(BigInteger, nullable=False)

    # Foreign key: links this document to the user who uploaded it
    # ForeignKey("users.id") means this column must match an id in the users table
    # ondelete="CASCADE" means: if the user is deleted, delete all their documents too
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Auto-fills with the current timestamp when a new row is inserted
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # SQLAlchemy relationship — lets you do document.owner to get the User object
    # back_populates="documents" connects this to the "documents" attribute on User
    # This does NOT create a column — it's Python-only, for convenience
    owner = relationship("User", back_populates="documents")

    # One document has many chunks
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
