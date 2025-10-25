"""
ゲーム作成・管理用のREST APIエンドポイント
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from app.game.services.game_service import game_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/games", tags=["games"])


# === Request/Response Models ===

class CreateSinglePlayRequest(BaseModel):
    """シングルプレイゲーム作成のリクエスト"""
    big_blind: int = Field(default=100, ge=10, le=1000, description="ビッグブラインド額")
    buy_in: int = Field(default=10000, ge=1000, le=100000, description="初期スタック額")


class CreateSinglePlayResponse(BaseModel):
    """シングルプレイゲーム作成のレスポンス"""
    game_id: str = Field(..., description="作成されたゲームのID")
    message: str = Field(..., description="結果メッセージ")
    ai_players: list[str] = Field(..., description="AIプレイヤーの名前リスト")
    websocket_url: str = Field(..., description="WebSocket接続URL")
class GameStateResponse(BaseModel):
    """ゲーム状態のレスポンス"""
    game_id: str = Field(..., description="ゲームID")
    status: str = Field(..., description="ゲーム状態")
    player_count: int = Field(..., description="プレイヤー数")
    seated_count: int = Field(..., description="着席数")


# === Endpoints ===

@router.post("/single-play", response_model=CreateSinglePlayResponse, status_code=status.HTTP_201_CREATED)
async def create_single_play_game(request: CreateSinglePlayRequest = CreateSinglePlayRequest()):
    """
    シングルプレイ用のゲームを作成
    
    - AI 2名が自動的に追加され、座席1と2に配置
    - 人間プレイヤーはWebSocket接続時に座席0に配置
    - 返されたgame_idとusernameを使用してWebSocketに接続
    
    Returns:
        CreateSinglePlayResponse: ゲーム情報とWebSocket URL
    """
    try:
        logger.info(f"Creating single play game: big_blind={request.big_blind}, buy_in={request.buy_in}")
        
        # シングルプレイゲームを作成
        game = await game_service.create_single_play_game(
            big_blind=request.big_blind,
            buy_in=request.buy_in
        )
        
        # AIプレイヤーの名前を取得
        ai_players = [p.name for p in game.players if p.is_ai]
        
        websocket_url = f"/ws/game/{game.id}?username=YOUR_USERNAME"
        
        logger.info(f"Game created: {game.id}, AI players: {ai_players}")
        
        return CreateSinglePlayResponse(
            game_id=game.id,
            message="Single play game created successfully",
            ai_players=ai_players,
            websocket_url=websocket_url
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{game_id}", response_model=GameStateResponse)
async def get_game_info(game_id: str):
    """
    ゲームの基本情報を取得
    
    Args:
        game_id: ゲームID
        
    Returns:
        GameStateResponse: ゲームの基本情報
    """
    game = game_service.get_game_state(game_id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    
    # 座席数をカウント
    seated_count = sum(1 for seat in game.table.seats if seat.is_occupied)
    
    return GameStateResponse(
        game_id=game.id,
        status=game.status.value,
        player_count=len(game.players),
        seated_count=seated_count
    )


@router.delete("/{game_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_game(game_id: str):
    """
    ゲームを削除
    
    Args:
        game_id: ゲームID
    """
    if game_id not in game_service.games:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    
    del game_service.games[game_id]
    logger.info(f"Game deleted: {game_id}")

