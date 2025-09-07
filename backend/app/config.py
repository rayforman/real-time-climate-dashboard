"""
Configuration management for Real-Time Climate Dashboard
Handles all environment variables and application settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings with validation and type safety"""
    
    # Application
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    DEBUG: bool = Field(default=True, description="Enable debug mode")
    API_HOST: str = Field(default="0.0.0.0", description="API host address")
    API_PORT: int = Field(default=8000, description="API port")
    LOG_LEVEL: str = Field(default="DEBUG", description="Logging level")
    
    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    DATABASE_POOL_SIZE: int = Field(default=20, description="Database connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=30, description="Database connection overflow")
    
    # Redis
    REDIS_URL: str = Field(..., description="Redis connection string")
    REDIS_MAX_CONNECTIONS: int = Field(default=50, description="Redis connection pool size")
    
    # Security
    SECRET_KEY: str = Field(..., description="JWT secret key for token signing")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="JWT token expiration")
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1", "*"],
        description="Allowed host headers"
    )
    
    # External APIs
    NOAA_BASE_URL: str = Field(
        default="https://www.ndbc.noaa.gov/data/realtime2",
        description="NOAA real-time data API base URL"
    )
    NOAA_REQUEST_TIMEOUT: int = Field(default=30, description="NOAA API request timeout (seconds)")
    NOAA_RETRY_ATTEMPTS: int = Field(default=3, description="NOAA API retry attempts")
    
    # OpenAI Integration (optional)
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key for insights")
    OPENAI_MODEL: str = Field(default="gpt-4", description="OpenAI model to use")
    
    # Geocoding (optional)
    MAPBOX_API_KEY: Optional[str] = Field(default=None, description="Mapbox API key for geocoding")
    
    # Cache TTL Settings (seconds)
    CACHE_LATEST_READING_TTL: int = Field(default=360, description="Latest reading cache TTL (6 minutes)")
    CACHE_BUOY_METADATA_TTL: int = Field(default=3600, description="Buoy metadata cache TTL (1 hour)")
    CACHE_USER_SESSION_TTL: int = Field(default=1800, description="User session cache TTL (30 minutes)")
    CACHE_POPULAR_BUOYS_TTL: int = Field(default=900, description="Popular buoys cache TTL (15 minutes)")
    CACHE_ALERT_STATES_TTL: int = Field(default=60, description="Alert states cache TTL (1 minute)")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="API rate limit per minute per IP")
    RATE_LIMIT_BURST: int = Field(default=10, description="Rate limit burst allowance")
    
    # Data Processing
    MAX_HISTORICAL_DAYS: int = Field(default=30, description="Maximum days of historical data to return")
    DATA_VALIDATION_TOLERANCE: float = Field(default=0.1, description="Data validation tolerance percentage")
    ANOMALY_DETECTION_THRESHOLD: float = Field(default=2.0, description="Standard deviations for anomaly detection")
    
    # Alert Thresholds
    HIGH_WAVE_THRESHOLD: float = Field(default=4.0, description="Wave height threshold for alerts (meters)")
    HIGH_WIND_THRESHOLD: float = Field(default=25.0, description="Wind speed threshold for alerts (mph)")
    LOW_PRESSURE_THRESHOLD: float = Field(default=1000.0, description="Low pressure threshold (millibars)")
    
    # Performance
    API_RESPONSE_TIMEOUT: int = Field(default=30, description="API response timeout (seconds)")
    WEBSOCKET_HEARTBEAT_INTERVAL: int = Field(default=30, description="WebSocket heartbeat interval (seconds)")
    
    # Monitoring
    ENABLE_METRICS: bool = Field(default=True, description="Enable Prometheus metrics collection")
    METRICS_PORT: int = Field(default=9090, description="Prometheus metrics port")
    
    # File paths
    BASE_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    LOGS_DIR: Path = Field(default_factory=lambda: Path("logs"))
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Validate environment setting"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level setting"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        """Validate secret key strength"""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        """Validate database URL format"""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v
    
    @validator("REDIS_URL")
    def validate_redis_url(cls, v):
        """Validate Redis URL format"""
        if not v.startswith("redis://"):
            raise ValueError("REDIS_URL must be a Redis connection string")
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT == "production"
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic migrations"""
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        
        # Example values for documentation
        schema_extra = {
            "example": {
                "ENVIRONMENT": "development",
                "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/climate",
                "REDIS_URL": "redis://localhost:6379/0",
                "SECRET_KEY": "your-super-secret-key-change-this-in-production",
                "NOAA_BASE_URL": "https://www.ndbc.noaa.gov/data/realtime2"
            }
        }

# Create global settings instance
settings = Settings()

# Development-specific settings
if settings.is_development:
    # More verbose logging in development
    settings.LOG_LEVEL = "DEBUG"
    # Disable HTTPS requirements
    settings.CORS_ORIGINS.extend([
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000"
    ])

# Production-specific settings
if settings.is_production:
    # More restrictive settings for production
    settings.DEBUG = False
    settings.LOG_LEVEL = "INFO"
    # Remove localhost from allowed hosts
    settings.ALLOWED_HOSTS = [host for host in settings.ALLOWED_HOSTS if host not in ["*", "localhost", "127.0.0.1"]]