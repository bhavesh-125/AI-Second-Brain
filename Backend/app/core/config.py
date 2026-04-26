from pathlib import Path
from pydantic_settings import BaseSettings

# This points to your backend folder
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str

    # JWT settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Upload settings
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10

    class Config:
        # Tell pydantic-settings where to find your .env file
        env_file = str(BASE_DIR / ".env")

# Create a single shared settings instance.
# Every other file imports THIS object — they never read .env directly.
settings = Settings()
