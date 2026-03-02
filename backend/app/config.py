from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite+aiosqlite:////tmp/prices.db"

    # Auth
    secret_key: str = "change-me-to-a-random-32-character-string"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    algorithm: str = "HS256"

    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    from_email: str = "no-reply@yourapp.com"

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_pro_price_id: str = ""
    stripe_enterprise_price_id: str = ""

    # Frontend URL
    frontend_url: str = "http://localhost:5173"

    # External price APIs
    pokemontcg_api_key: str = ""
    ebay_client_id: str = ""
    ebay_client_secret: str = ""
    pricecharting_api_key: str = ""

    # Free tier limits
    free_tier_daily_searches: int = 20
    pro_watchlist_limit: int = 100

    # Marketplace
    commission_rate: float = 0.06


settings = Settings()
