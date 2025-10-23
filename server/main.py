"""
FastAPIアプリケーションのエントリーポイント
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.websocket import chat_router, game_router
import logging
import os

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション作成
app = FastAPI(
    title="Online Poker Game",
    description="FastAPI + WebSocketを使用したオンラインポーカーゲーム",
    version="1.0.0"
)

# CORS設定 (React開発サーバーからのアクセスを許可)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default port
        "http://localhost:3000",  # alternative port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocketルーターを追加
app.include_router(chat_router, tags=["WebSocket Chat"])
app.include_router(game_router, tags=["WebSocket Game"])

# 静的ファイルの提供（React本番ビルド用）
# client/distディレクトリが存在する場合のみマウント
client_dist_path = os.path.join(os.path.dirname(__file__), "..", "client", "dist")
if os.path.exists(client_dist_path):
    app.mount("/", StaticFiles(directory=client_dist_path, html=True), name="client")
    logger.info(f"Serving client from: {client_dist_path}")
else:
    logger.warning(f"Client dist directory not found: {client_dist_path}")
    logger.info("Run 'npm run build' in the client directory to build the React app")

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy", "service": "poker"}


@app.get("/api/info")
async def api_info():
    """API情報エンドポイント"""
    return {
        "name": "Online Poker Game API",
        "version": "1.0.0",
        "websocket_endpoints": {
            "chat": "/ws/chat/{room_id}",
        }
    }


if __name__ == "__main__":
    import uvicorn
    # 0.0.0.0 にすることで、同じネットワーク内の他の端末からもアクセス可能になります
    uvicorn.run(app, host="0.0.0.0", port=8000)
