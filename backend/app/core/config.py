from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Portfolio Reporting Studio"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7
    database_url: str = "postgresql://prs:prs@db:5432/prs"
    redis_url: str = "redis://redis:6379/0"
    environment: str = "dev"
    runway_risk_threshold: float = 6.0
    revenue_drop_threshold: float = -0.1
    margin_drop_threshold: float = -0.1


settings = Settings()
