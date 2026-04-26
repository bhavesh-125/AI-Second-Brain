# backend/app/models/user.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)

    # We never store the real password — only the bcrypt hash of it
    hashed_password = Column(String, nullable=False)

    is_active = Column(Boolean, default=True)

    # server_default=func.now() means PostgreSQL itself fills this in at insert time
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # onupdate=func.now() means this column auto-updates whenever the row changes
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # NEW: the other side of the relationship defined in Document
    # "Document" refers to the Document class (SQLAlchemy finds it by name)
    # back_populates="owner" must match the relationship name inside Document
    # This lets you do: user.documents to get all their uploaded files
    documents = relationship("Document", back_populates="owner")
