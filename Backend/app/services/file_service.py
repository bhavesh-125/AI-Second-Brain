import os
import uuid
from pathlib import Path

from fastapi import UploadFile, HTTPException, status

from app.core.config import settings


# Allowed file types and their saved extensions
ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "text/markdown": ".md",
}


# Convert MB into bytes
MAX_FILE_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024


def get_upload_dir() -> Path:
    # Get upload folder path
    upload_path = Path(settings.UPLOAD_DIR)

    # Create folder if it does not exist
    upload_path.mkdir(parents=True, exist_ok=True)

    # Return folder path
    return upload_path


def validate_file(file: UploadFile) -> None:
    # Check whether file type is allowed
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, TXT, and Markdown files are allowed"
        )


async def save_upload_file(file: UploadFile) -> dict:
    # Read uploaded file content
    file_content = await file.read()

    # Get file size in bytes
    file_size = len(file_content)

    # Reject empty file
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot upload an empty file"
        )

    # Reject file larger than allowed size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds {settings.MAX_FILE_SIZE_MB} MB limit"
        )

    # Get correct extension from MIME type
    extension = ALLOWED_TYPES[file.content_type]

    # Create unique filename to avoid overwrite
    stored_filename = f"{uuid.uuid4()}{extension}"

    # Get upload directory
    upload_dir = get_upload_dir()

    # Create final file path
    file_path = upload_dir / stored_filename

    # Save file to disk
    with open(file_path, "wb") as f:
        f.write(file_content)

    # Return file metadata
    return {
        "stored_filename": stored_filename,
        "file_path": str(file_path),
        "file_size": file_size,
    }


def delete_file_from_disk(file_path: str) -> None:
    # Try deleting file from disk
    try:
        os.remove(file_path)

    # Ignore if file is already missing
    except FileNotFoundError:
        pass