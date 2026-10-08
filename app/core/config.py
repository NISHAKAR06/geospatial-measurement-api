from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Geospatial Measurement API"
    API_V1_PREFIX: str = "/api"
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/geospatial"
    MAX_UPLOAD_SIZE_MB: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

