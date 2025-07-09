"""Configuration management for Exercise Service."""

from typing import List, Optional
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import json


class Settings(BaseSettings):
    """Application settings with validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    # Application
    APP_NAME: str = "Spool Exercise Service"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production)$")
    SERVICE_NAME: str = "exercise-service"
    SERVICE_PORT: int = 8003
    
    # OpenAI
    OPENAI_API_KEY: str
    EVALUATION_MODEL: str = "gpt-4o"
    GENERATION_MODEL: str = "gpt-4o"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 2000
    
    # LangChain (optional)
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_PROJECT: str = "spool-exercise-service"
    
    # Service URLs
    CONTENT_SERVICE_URL: str = "http://localhost:8002"
    PROFILE_SERVICE_URL: str = "http://localhost:8004"
    API_GATEWAY_URL: str = "http://localhost:8000"
    
    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL: int = 3600  # 1 hour
    EXERCISE_CACHE_TTL: int = 86400  # 24 hours
    
    # LangGraph
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0
    WORKFLOW_TIMEOUT: int = 120  # seconds
    
    # Exercise Configuration
    MIN_RESPONSE_LENGTH: int = 50
    MAX_RESPONSE_LENGTH: int = 2000
    EVALUATION_CONFIDENCE_THRESHOLD: float = 0.7
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    LOG_FORMAT: str = Field(default="json", pattern="^(json|plain)$")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(default_factory=list)
    
    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 50
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Monitoring
    ENABLE_METRICS: bool = True
    
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()