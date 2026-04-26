import fitz   # this is PyMuPDF — confusingly, the package installs as "fitz"
from pathlib import Path
from typing import List


# --- Chunking configuration ---
# These numbers are carefully chosen for RAG performance.
# Too large = chunk contains too many topics, retrieval is noisy.
# Too small = chunk loses context, answers are incomplete.

CHUNK_SIZE = 500        # target size of each chunk in characters
CHUNK_OVERLAP = 100     # how many characters to repeat between consecutive chunks


def extract_text_from_file(file_path: str, file_type: str) -> str:
    """
    Reads a file from disk and returns its full text content as a plain string.
    Handles PDF files differently from plain text files.

    Args:
        file_path: absolute or relative path to the file on disk
        file_type: MIME type e.g. "application/pdf" or "text/plain"

    Returns:
        A single string with all the text from the file.
        Returns empty string if extraction fails (we log but don't crash).
    """
    path = Path(file_path)

    if not path.exists():
        # File was deleted from disk after upload — shouldn't happen, but be safe
        raise FileNotFoundError(f"File not found at path: {file_path}")

    if file_type == "application/pdf":
        return _extract_pdf_text(file_path)
    else:
        # text/plain and text/markdown are both readable with open()
        return _extract_plain_text(file_path)


def _extract_pdf_text(file_path: str) -> str:
    """
    Opens a PDF with PyMuPDF and extracts all text, page by page.
    We add a newline between pages so paragraph boundaries are preserved.
    """
    text_parts = []

    # fitz.open() loads the PDF into memory
    with fitz.open(file_path) as pdf_document:
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]

            # get_text() returns a string of all text on this page.
            # PyMuPDF handles columns, multi-line paragraphs, and headers correctly.
            page_text = page.get_text()

            if page_text.strip():   # skip blank pages
                text_parts.append(page_text)

    # Join pages with double newline so paragraphs don't merge across pages
    return "\n\n".join(text_parts)


def _extract_plain_text(file_path: str) -> str:
    """
    Reads a .txt or .md file as plain text.
    errors="replace" means bad characters become ? instead of crashing.
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def split_text_into_chunks(text: str) -> List[str]:
    """
    Splits a long string of text into smaller overlapping chunks.

    WHY OVERLAP?
    Imagine a sentence that spans the boundary between two chunks.
    Without overlap, the sentence is split in half — both chunks are incomplete.
    With overlap, that sentence appears in full in at least one chunk,
    so the AI can always find it intact.

    Example with CHUNK_SIZE=20, CHUNK_OVERLAP=5:
    Text:    "The quick brown fox jumps over"
    Chunk 0: "The quick brown fox "   (chars 0–19)
    Chunk 1: "fox jumps over"          (chars 15–end, starting 5 chars back)

    Args:
        text: the full extracted document text

    Returns:
        A list of strings, each roughly CHUNK_SIZE characters long.
        Returns [] if the text is empty or whitespace only.
    """
    # Normalize whitespace — collapse multiple spaces/newlines into single spaces
    text = " ".join(text.split())

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        # Calculate where this chunk ends
        end = start + CHUNK_SIZE

        if end >= len(text):
            # This is the last chunk — take everything remaining
            chunk = text[start:]
        else:
            # Try to find a natural break point (space) near the chunk boundary.
            # This prevents cutting words in half.
            # We search backwards from `end` for the nearest space.
            break_point = text.rfind(" ", start, end)

            if break_point == -1:
                # No space found — just cut at CHUNK_SIZE (rare, e.g. very long URL)
                break_point = end

            chunk = text[start:break_point]

        # Only add non-empty chunks
        if chunk.strip():
            chunks.append(chunk.strip())

        # Move forward by (CHUNK_SIZE - CHUNK_OVERLAP) to create the overlap
        # e.g. if CHUNK_SIZE=500 and CHUNK_OVERLAP=100, next chunk starts at char 400
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks