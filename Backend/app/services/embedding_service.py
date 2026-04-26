from typing import List, Optional

from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.chunk import DocumentChunk


# Embedding model name
# This model creates 768-dimensional vectors
EMBEDDING_MODEL_NAME = "BAAI/bge-base-en-v1.5"


# Load model once when app starts
# Loading once is better than loading on every request
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)


def create_embedding(input_text: str) -> List[float]:
    """
    Convert text into a 768-dimensional embedding vector.
    """

    # Clean input text
    cleaned_text = input_text.replace("\n", " ").strip()

    # BGE models work better when retrieval queries are prefixed like this
    # For document chunks, normal text is okay
    embedding = embedding_model.encode(
        cleaned_text,
        normalize_embeddings=True
    )

    # Convert numpy array to normal Python list
    return embedding.tolist()


def create_query_embedding(query: str) -> List[float]:
    """
    Convert user search query into embedding.
    BGE recommends adding this prefix for search queries.
    """

    # Query instruction improves retrieval quality for BGE models
    query_text = f"Represent this sentence for searching relevant passages: {query}"

    embedding = embedding_model.encode(
        query_text,
        normalize_embeddings=True
    )

    return embedding.tolist()


def embed_chunks_for_document(document_id: int, db: Session) -> int:
    """
    Find all chunks of a document without embeddings,
    create embeddings, and save them in PostgreSQL.
    """

    # Get chunks that don't have embeddings yet
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .filter(DocumentChunk.embedding == None)  # noqa: E711
        .all()
    )

    embedded_count = 0

    # Generate embedding for each chunk
    for chunk in chunks:
        try:
            # Create vector for chunk content
            vector = create_embedding(chunk.content)

            # Save vector in pgvector column
            chunk.embedding = vector

            embedded_count += 1

        except Exception as error:
            # If one chunk fails, continue with others
            print(f"Embedding failed for chunk {chunk.id}: {error}")

    # Save all embeddings to DB
    db.commit()

    return embedded_count


def search_similar_chunks(
    query: str,
    user_id: int,
    db: Session,
    top_k: int = 5,
    document_id: Optional[int] = None
):
    """
    Search most similar chunks using pgvector cosine distance.
    """

    # Convert query to vector
    query_vector = create_query_embedding(query)

    # Optional document filter
    document_filter = ""
    if document_id is not None:
        document_filter = "AND document_id = :document_id"

    # pgvector cosine distance operator: <=>
    # Smaller distance = more similar
    # similarity = 1 - distance
    sql = f"""
        SELECT
            id AS chunk_id,
            document_id,
            chunk_index,
            content,
            1 - (embedding <=> CAST(:query_vector AS vector)) AS similarity
        FROM document_chunks
        WHERE
            user_id = :user_id
            AND embedding IS NOT NULL
            {document_filter}
        ORDER BY embedding <=> CAST(:query_vector AS vector)
        LIMIT :top_k;
    """

    params = {
        "query_vector": str(query_vector),
        "user_id": user_id,
        "top_k": top_k,
    }

    if document_id is not None:
        params["document_id"] = document_id

    results = db.execute(text(sql), params).fetchall()

    return [
        {
            "chunk_id": row.chunk_id,
            "document_id": row.document_id,
            "chunk_index": row.chunk_index,
            "content": row.content,
            "similarity": round(float(row.similarity), 4),
        }
        for row in results
    ]