from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration with environment variable support."""

    # Database
    database_url: str = "postgresql+asyncpg://raguser:ragpass@localhost:5432/ragdb"

    # Ollama
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # Embedding Model
    embed_model_path: str = "/models/bge-m3"
    embed_device: str = "cpu"  # or "cuda" for GPU acceleration
    embed_batch_size: int = 32

    # Text Chunking
    chunk_size: int = 512
    chunk_overlap: int = 128

    # Retrieval
    top_k: int = 5
    score_threshold: float = 0.5

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # or "text"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
