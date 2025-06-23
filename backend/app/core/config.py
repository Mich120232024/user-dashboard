"""Application configuration using Pydantic Settings."""

from typing import List, Optional, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application Settings
    app_name: str = "User Dashboard API"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS Configuration
    backend_cors_origins: List[AnyHttpUrl] = []
    
    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        elif isinstance(v, str):
            # Handle JSON string
            import json
            return json.loads(v)
        raise ValueError(v)
    
    # Database Configuration (Cosmos DB)
    cosmos_endpoint: str = "https://your-cosmos-account.documents.azure.com:443/"
    cosmos_key: str = "your-cosmos-key-here"
    cosmos_database_name: str = "user_dashboard"
    use_cosmos_mongodb_api: bool = False
    cosmos_mongodb_connection_string: str = "mongodb://your-cosmos-account:key@your-cosmos-account.mongo.cosmos.azure.com:10255/?ssl=true"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # Azure Storage Configuration
    azure_storage_connection_string: Optional[str] = None
    
    # JWT Configuration
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # External Services
    agent_management_api_url: Optional[AnyHttpUrl] = None
    message_service_api_url: Optional[AnyHttpUrl] = None
    
    # Azure Blob Storage
    azure_storage_account_name: Optional[str] = None
    azure_storage_container_name: Optional[str] = None
    azure_storage_connection_string: Optional[str] = None
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"  # json or plain
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    # Feature Flags
    enable_websockets: bool = True
    enable_metrics: bool = True
    enable_cache: bool = True
    
    # Cache Configuration
    cache_ttl: int = 300  # seconds
    
    # WebSocket Configuration
    ws_heartbeat_interval: int = 30  # seconds
    ws_connection_timeout: int = 60  # seconds


# Create global settings instance
settings = Settings()