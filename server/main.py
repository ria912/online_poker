"""
FastAPIアプリケーションのエントリーポイント
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.websocket import router as websocket_router
from app.api.game_api import router as game_api_router
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

# テンプレート設定
templates = Jinja2Templates(directory="templates")

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

# ルーターを追加
app.include_router(game_api_router)  # REST API
app.include_router(websocket_router)  # WebSocket


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """テストクライアントのHTMLページを表示"""
    return templates.TemplateResponse("index.html", {"request": request})


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
        "description": "Texas Hold'em Poker single play with AI opponents",
        "endpoints": {
            "rest_api": {
                "create_game": "POST /api/games/single-play",
                "get_game": "GET /api/games/{game_id}",
                "delete_game": "DELETE /api/games/{game_id}"
            },
            "websocket": {
                "game": "WS /ws/game/{game_id}?username={username}"
            }
        },
        "usage": {
            "step1": "POST /api/games/single-play to create a game",
            "step2": "Connect to WS /ws/game/{game_id}?username=YOUR_NAME",
            "step3": "Send {type: 'start_game'} to begin",
            "step4": "Send {type: 'player_action', action: 'CALL|CHECK|FOLD', amount: 0} to play"
        },
        "test_client": "http://localhost:8000/ for interactive test client"
    }


# 静的ファイルの提供（React本番ビルド用）
# client/distディレクトリが存在する場合のみマウント
client_dist_path = os.path.join(os.path.dirname(__file__), "..", "client", "dist")
if os.path.exists(client_dist_path):
    app.mount("/client", StaticFiles(directory=client_dist_path, html=True), name="client")
    logger.info(f"Serving client from: {client_dist_path}")
else:
    logger.warning(f"Client dist directory not found: {client_dist_path}")
    logger.info("Run 'npm run build' in the client directory to build the React app")


if __name__ == "__main__":
    import uvicorn
    # 0.0.0.0 にすることで、同じネットワーク内の他の端末からもアクセス可能になります
    uvicorn.run(app, host="0.0.0.0", port=8000)
