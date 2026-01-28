"""
Configuration Management for LectureBot
"""
import os
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    
    # AWS Cognito Configuration
    aws_region: str = "us-east-1"
    cognito_user_pool_id: str = ""
    cognito_app_client_id: str = ""
    cognito_app_client_secret: str = ""
    
    # Application Settings
    app_title: str = "LectureBot - AI Study Assistant"
    max_file_size_mb: int = 50
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Vector Store
    vector_store_type: Literal["faiss"] = "faiss"
    persist_directory: str = "./vectorstore"
    
    # Model Configuration
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.3
    max_tokens: int = 2000
    
    # Search Configuration
    top_k_results: int = 5
    search_type: Literal["similarity", "mmr"] = "similarity"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes"""
        return self.max_file_size_mb * 1024 * 1024


# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"
LOGS_DIR = BASE_DIR / "logs"

# Create directories
for directory in [DATA_DIR, UPLOADS_DIR, VECTORSTORE_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Initialize settings
settings = Settings()


def get_user_uploads_dir(session_id: str) -> Path:
    """Get user-scoped uploads directory"""
    user_dir = UPLOADS_DIR / session_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def get_user_vectorstore_dir(session_id: str) -> Path:
    """Get user-scoped vectorstore directory"""
    user_dir = VECTORSTORE_DIR / session_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir
