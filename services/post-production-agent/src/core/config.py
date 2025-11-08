from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # This class loads all variables from the environment (.env file)
    # Pydantic will raise a validation error if a required variable is missing.
    
    # Optional allows Pydantic to not require the variable if it's not needed by the service.
    # We use Field(default=None) to be explicit.
    GOOGLE_API_KEY: Optional[str] = Field(default=None)
    
    POSTGRES_USER: Optional[str] = Field(default=None)
    POSTGRES_PASSWORD: Optional[str] = Field(default=None)
    POSTGRES_DB: Optional[str] = Field(default=None)

    MINIO_ROOT_USER: Optional[str] = Field(default=None)
    MINIO_ROOT_PASSWORD: Optional[str] = Field(default=None)
    
    S3_ENDPOINT_URL: Optional[str] = Field(default=None)
    S3_ACCESS_KEY: Optional[str] = Field(default=None)
    S3_SECRET_KEY: Optional[str] = Field(default=None)
    S3_BUCKET_NAME: Optional[str] = Field(default=None)
    
    CELERY_BROKER_URL: Optional[str] = Field(default=None)
    
    CREATIVE_AGENT_URL: Optional[str] = Field(default=None)

    # This tells Pydantic to look for a .env file.
    # Docker Compose's `env_file` makes this redundant but it's good practice.
    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

settings = Settings()