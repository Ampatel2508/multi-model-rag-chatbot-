"""Application configuration and settings."""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self) -> None:
        """Initialize settings from environment variables."""
        # Server Configuration
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))

        # CORS Configuration
        cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
        self.CORS_ORIGINS: List[str] = [origin.strip() for origin in cors_origins_str.split(",")]

        # Upload Configuration
        self.UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
        self.MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
        self.ALLOWED_EXTENSIONS: List[str] = os.getenv(
            "ALLOWED_EXTENSIONS",
            ".pdf,.docx,.doc,.xlsx,.xls,.csv,.txt,.png,.jpg,.jpeg,.gif,.webp"
        ).split(",")

        # RAG Configuration
        self.CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
        self.CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
        self.RETRIEVER_K: int = int(os.getenv("RETRIEVER_K", "5"))


# Singleton instance
settings: Settings = Settings()