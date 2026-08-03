from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "change-me-to-a-long-random-string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    DATABASE_URL: str = "sqlite:///./grahika.db"
    CORS_ORIGINS: str = "http://localhost:4200"

    # Default ayanamsa applied when a chart request doesn't specify one.
    DEFAULT_AYANAMSA: str = "lahiri"

    class Config:
        env_file = ".env"


settings = Settings()
