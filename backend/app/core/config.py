"""LabLens AI - Core Configuration"""
from typing import List, Optional
from functools import lru_cache

try:
    # pydantic v2 provides BaseSettings in pydantic_settings; fall back to pydantic for v1 compatibility
    from pydantic_settings import BaseSettings  # type: ignore
except Exception:
    from pydantic import BaseSettings  # type: ignore


class Settings(BaseSettings):
    app_name: str = "LabLens AI"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "production"

    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    database_url: str = "postgresql://localhost/lablens"

    storage_endpoint: Optional[str] = None
    storage_bucket: str = "lablens-reports"
    storage_access_key: Optional[str] = None
    storage_secret_key: Optional[str] = None
    storage_region: str = "us-east-1"
    storage_use_ssl: bool = True

    ai_provider: str = "openai"
    ai_api_key: Optional[str] = None
    ai_base_url: Optional[str] = None
    ai_model: str = "gpt-4o"
    ai_vision_model: str = "gpt-4o"
    ai_temperature: float = 0.1
    ai_max_tokens: int = 4096

    ocr_provider: str = "tesseract"
    ocr_api_key: Optional[str] = None
    ocr_endpoint: Optional[str] = None

    max_upload_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: List[str] = ["pdf", "jpg", "jpeg", "png"]
    encryption_key: Optional[str] = None

    frontend_url: str = "http://localhost:5173"

    log_level: str = "INFO"
    enable_audit_log: bool = True

    report_retention_days: int = 365
    auto_delete_after_days: int = 1095

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
