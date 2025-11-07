"""
Configuration management for Orchestrator.
Centralizes all settings with environment variable support and validation.
"""
import logging
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings with strict validation."""
    
    # === API Settings ===
    app_name: str = "Agent Orchestrator"
    app_version: str = "2.0.0"
    api_prefix: str = "/api/v2"
    debug: bool = Field(default=False)
    environment: str = Field(default="development")
    
    # === Server Settings ===
    orchestrator_host: str = Field(default="0.0.0.0")
    orchestrator_port: int = Field(default=8000)
    
    # === Logging ===
    log_level: str = Field(default="INFO")
    
    # === Database (PostgreSQL) ===
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_user: str = Field(default="agent_user")
    postgres_password: str = Field(default="agent_pass")
    postgres_db: str = Field(default="agent_db")
    postgres_schema: str = Field(default="agent_system")
    
    # === Redis ===
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    redis_password: Optional[str] = Field(default=None)
    
    # === Anthropic (Primary) ===
    anthropic_api_key: str = Field(default="")
    anthropic_model: str = Field(default="claude-sonnet-4-20250514")
    anthropic_max_tokens: int = Field(default=2000)
    anthropic_temperature: float = Field(default=0.7)
    
    # === OpenAI (Fallback) ===
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4-turbo-preview")
    openai_max_tokens: int = Field(default=2000)
    openai_temperature: float = Field(default=0.7)
    
    # === LLM Fallback Strategy ===
    llm_primary_provider: str = Field(default="anthropic")  # "anthropic" | "openai"
    llm_fallback_provider: str = Field(default="openai")
    llm_fallback_enabled: bool = Field(default=True)
    llm_max_retries: int = Field(default=3)
    llm_circuit_breaker_threshold: int = Field(default=5)  # failures before switching
    llm_cache_ttl: int = Field(default=7200)  # Cache TTL in seconds (2 hours)
    
    # === Token Budget ===
    daily_token_budget: int = Field(default=100000)
    llm_token_budget_sprint: int = Field(default=5000000)  # Sprint-level budget
    token_alert_threshold: float = Field(default=0.8)  # 80%
    token_tracking_enabled: bool = Field(default=True)
    
    # === Agent Settings ===
    task_timeout_seconds: int = Field(default=300)
    max_retry_count: int = Field(default=3)
    consumer_group_name: str = Field(default="orchestrator_group")
    
    # === Health Check ===
    health_check_interval: int = Field(default=30)
    
    # === Redis Streams ===
    stream_task_key: str = Field(default="tasks:stream")
    stream_result_key: str = Field(default="results:stream")
    stream_max_len: int = Field(default=10000)
    
    @property
    def database_url(self) -> str:
        """Construct async PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    # === Pydantic V2 Field Validators ===
    
    @field_validator("anthropic_api_key", "openai_api_key")
    @classmethod
    def validate_api_keys(cls, v: str, info) -> str:
        """Validate API key format (warn if empty)."""
        field_name = info.field_name
        if field_name == "anthropic_api_key" and not v:
            logger.warning("⚠️  Anthropic API key is empty - LLM features will be limited")
        if field_name == "openai_api_key" and not v:
            logger.warning("⚠️  OpenAI API key is empty - Fallback will be unavailable")
        return v
    
    @field_validator("daily_token_budget", "llm_token_budget_sprint")
    @classmethod
    def validate_token_budget(cls, v: int, info) -> int:
        """Ensure token budget is reasonable."""
        if v < 1000:
            raise ValueError(f"{info.field_name} must be at least 1000")
        if v > 10000000:
            raise ValueError(f"{info.field_name} exceeds safe limit (10M tokens)")
        return v
    
    @field_validator("llm_primary_provider", "llm_fallback_provider")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        """Validate LLM provider is supported."""
        valid_providers = ["anthropic", "openai"]
        if v not in valid_providers:
            raise ValueError(f"Invalid LLM provider: {v}. Must be one of {valid_providers}")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "env_prefix": "",
    }


# === Global Settings Instance ===
settings = Settings()