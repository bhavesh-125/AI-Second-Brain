from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.core.security import get_current_user
from app.services.embedding_service import search_similar_chunks


router = APIRouter(
    prefix="/search",
    tags=["Search"]
)


class SearchRequest(BaseModel):
    # User question/search text
    query: str

    # Number of chunks to return
    top_k: int = 5

    # Optional: search only inside one document
    document_id: Optional[int] = None


@router.post("/")
def semantic_search(
    request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Reject empty query
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty"
        )

    # Limit top_k to prevent expensive requests
    if request.top_k < 1 or request.top_k > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="top_k must be between 1 and 20"
        )

    # Search similar chunks
    results = search_similar_chunks(
        query=request.query,
        user_id=current_user.id,
        db=db,
        top_k=request.top_k,
        document_id=request.document_id
    )

    return {
        "query": request.query,
        "total": len(results),
        "results": results
    }
