from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg://career_network:change-me@localhost:5432/career_network"
    )
    frontend_origin: str = "http://localhost:3000"
    trusted_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    secret_key: str = "replace-with-a-long-random-development-secret"
    session_cookie_name: str = "career_network_session"
    session_ttl_hours: int = 168
    cookie_secure: bool = False

    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
