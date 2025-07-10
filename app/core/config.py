"""Configuration management for Exercise Service."""

from typing import List, Optional, Any
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import json
import structlog

logger = structlog.get_logger()


class Settings(BaseSettings):
    """Application settings with validation."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )

    # Application
    APP_NAME: str = "Spool Exercise Service"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(
        default="development", pattern="^(development|staging|production)$"
    )
    SERVICE_NAME: str = "exercise-service"
    SERVICE_PORT: int = 8003

    # OpenAI - will be loaded from AWS Parameter Store in production
    OPENAI_API_KEY: str = Field(default="")
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

    # Pinecone Configuration
    PINECONE_API_KEY: str = Field(default="")
    PINECONE_INDEX_NAME: str = "spool-content"
    PINECONE_ENVIRONMENT: str = "us-east-1-aws"
    PINECONE_NAMESPACE: str = "content"
    PINECONE_TOP_K: int = 5

    # Content Service Integration
    CONTENT_SERVICE_SEARCH_URL: str = "http://localhost:8002/api/content/search"
    ENABLE_VECTOR_CONTEXT: bool = True

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
    LOG_LEVEL: str = Field(
        default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )
    LOG_FORMAT: str = Field(default="json", pattern="^(json|plain)$")

    # CORS
    CORS_ORIGINS: List[str] = Field(default_factory=list)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return list(parsed) if isinstance(parsed, list) else [str(parsed)]
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        if isinstance(v, list):
            return [str(item) for item in v]
        return []

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 50
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # Monitoring
    ENABLE_METRICS: bool = True

    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"

    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == "development"

    def load_production_secrets(self) -> None:
        """Load secrets from AWS Parameter Store for production."""
        if not self.is_production():
            return

        try:
            from app.core.aws_config import get_aws_parameter_store

            aws_params = get_aws_parameter_store()

            # Load OpenAI API key from AWS Parameter Store
            openai_key = aws_params.get_parameter("/spool/openai-api-key")
            if openai_key:
                self.OPENAI_API_KEY = openai_key
                logger.info("Loaded OpenAI API key from AWS Parameter Store")
            else:
                logger.error("Failed to load OpenAI API key from AWS Parameter Store")

            # Load Pinecone API key from AWS Parameter Store
            pinecone_key = aws_params.get_parameter("/spool/pinecone-api-key")
            if pinecone_key:
                self.PINECONE_API_KEY = pinecone_key
                logger.info("Loaded Pinecone API key from AWS Parameter Store")
            else:
                logger.warning("Pinecone API key not found in AWS Parameter Store")

        except Exception as e:
            logger.error("Failed to load production secrets", error=str(e))
            raise

    def validate_configuration(self) -> None:
        """Validate configuration based on environment."""
        if self.is_production():
            if not self.OPENAI_API_KEY or self.OPENAI_API_KEY.startswith("test"):
                raise ValueError("Production environment requires valid OpenAI API key")

        if self.is_development():
            # Allow test keys in development
            if not self.OPENAI_API_KEY:
                logger.warning("No OpenAI API key configured for development")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()

    # Load production secrets if in production
    if settings.is_production():
        settings.load_production_secrets()

    # Validate configuration
    settings.validate_configuration()

    return settings


# Global settings instance
settings = get_settings()
