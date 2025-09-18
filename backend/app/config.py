from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 데이터베이스 설정
    database_url: str = "postgresql://hooni1939:qweruiopyt1!@honi001.synology.me:9000/engagenow"
    redis_url: str = "redis://honi001.synology.me:9001"

    # 인증 설정
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # 보안 설정
    max_login_attempts: int = 5
    account_lockout_minutes: int = 30
    password_min_length: int = 8
    require_email_verification: bool = True

    # CORS 보안 설정
    allow_credentials: bool = True
    allowed_methods: list = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    allowed_headers: list = ["*"]

    # OAuth 설정
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: str = "http://localhost:8000/api/auth/callback/google"

    # OAuth 보안 설정
    oauth_state_secret: str = "oauth-state-secret-key"

    # 기타 설정
    debug: bool = False
    cors_origins: list = ["http://localhost:3000"]

    class Config:
        env_file = ".env"

settings = Settings()