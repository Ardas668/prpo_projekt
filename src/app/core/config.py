from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Akademie Trutnov - IS Kurzy"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    DB_HOST: str = Field(default="localhost", alias="DB_HOST")
    DB_PORT: int = Field(default=5432, alias="DB_PORT")
    DB_USER: str = Field(default="postgres", alias="DB_USER")
    DB_PASSWORD: str = Field(default="postgres", alias="DB_PASSWORD")
    DB_NAME: str = Field(default="akademie_db", alias="DB_NAME")
    DATABASE_URL: str | None = None

    # Jednoduché přihlášení pro školní projekt (konfigurovatelné přes .env)
    ADMIN_EMAIL: str = Field(default="admin@akademietrutnov.cz", alias="ADMIN_EMAIL")
    ADMIN_PASSWORD: str = Field(default="admin123", alias="ADMIN_PASSWORD")
    LECTURER_DEMO_PASSWORD: str = Field(default="lektor123", alias="LECTURER_DEMO_PASSWORD")
    STUDENT_DEMO_PASSWORD: str = Field(default="student123", alias="STUDENT_DEMO_PASSWORD")

    @property
    def sync_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = {"env_file": ".env", "extra": "allow"}

settings = Settings()
