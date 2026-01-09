from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram Bot
    bot_token: str

    # PostgreSQL
    postgres_user: str = "dreambot"
    postgres_password: str
    postgres_db: str = "dreamdiary"
    postgres_host: str = "db"
    postgres_port: int = 5432

    # Pagination
    dreams_per_page: int = 5

    @property
    def database_url(self) -> str:
        """Construct async PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
