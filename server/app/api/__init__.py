from fastapi import APIRouter
from .router import router as game_router

# メインAPIルーター
router = APIRouter()

# 各機能のルーターを追加
router.include_router(game_router, prefix="/games", tags=["games"])
