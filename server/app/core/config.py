from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="server/.env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./mentos.db"
    jwt_secret: str = "dev-secret"
    jwt_access_minutes: int = 15
    refresh_token_days: int = 30
    apple_audience: str = "com.example.mentos"
    token_encryption_key_b64: str
    debug: bool = True
    admin_sub_allowlist: str = ""
    cors_origins: str = "http://localhost:3000"

    apns_team_id: str = ""
    apns_key_id: str = ""
    apns_auth_key_p8: str = ""
    apns_auth_key_path: str = ""
    apns_bundle_id: str = "com.example.mentos"
    apns_use_sandbox: bool = True

    monzo_client_id: str = ""
    monzo_client_secret: str = ""
    monzo_redirect_uri: str = "mentos://oauth/monzo"
    monzo_auth_url: str = "https://auth.monzo.com/"
    monzo_token_url: str = "https://api.monzo.com/oauth2/token"
    monzo_scopes: str = "accounts balance:read transactions:read"


@lru_cache
def get_settings() -> Settings:
    return Settings()
