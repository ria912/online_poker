from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import router as api_router
from app.websocket import router as websocket_router


def create_app() -> FastAPI:
    """FastAPIアプリケーションのファクトリ関数"""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description=settings.description,
        debug=settings.debug,
    )
    
    # CORS設定
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ルーター登録
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(websocket_router, prefix="/ws")
    
    @app.get("/")
    async def root():
        """ヘルスチェックエンドポイント"""
        return {
            "message": "Online Poker Game API",
            "version": settings.version,
            "status": "running"
        }
    
    @app.get("/health")
    async def health_check():
        """ヘルスチェック"""
        return {"status": "healthy"}
    
    return app


# アプリケーションインスタンス
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )