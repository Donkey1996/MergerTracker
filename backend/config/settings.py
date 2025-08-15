from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Database
    DATABASE_URL: str = "postgresql://mergertracker:mergertracker_password@localhost:5432/mergertracker"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # API Configuration
    API_BASE_URL: str = "http://localhost:8000"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "*"]
    
    # AI Configuration
    CLAUDE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    DEFAULT_LLM_PROVIDER: str = "claude"
    MAX_TOKENS_PER_REQUEST: int = 4000
    AI_CONFIDENCE_THRESHOLD: float = 0.8
    
    # Scraping Configuration
    SCRAPING_DELAY: int = 2
    USER_AGENT_ROTATION: bool = True
    PROXY_ENABLED: bool = False
    SCRAPING_RATE_LIMIT: int = 1
    
    # Rate Limiting
    API_RATE_LIMIT: int = 100
    
    # Logging
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None
    
    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()