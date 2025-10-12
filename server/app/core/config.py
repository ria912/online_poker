from pydantic import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # アプリケーション基本設定
    app_name: str = "Online Poker Game"
    version: str = "1.0.0"
    description: str = "Online Poker Game with FastAPI and WebSocket"
    
    # サーバー設定
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # データベース設定
    database_url: str = "sqlite+aiosqlite:///./poker_game.db"
    
    # セキュリティ設定
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS設定
    allowed_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Redis設定（将来のセッション管理用）
    redis_url: Optional[str] = None
    
    class Config:
        env_file = ".env"


# グローバル設定インスタンス
settings = Settings()