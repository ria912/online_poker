"""
ゲーム用WebSocketエンドポイント
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from .game_manager import game_manager
import logging
import json

logger = logging.getLogger(__name__)

game_router = APIRouter()


@game_router.websocket("/ws/game/{game_id}")
async def websocket_game_endpoint(
    websocket: WebSocket,
    game_id: str,
    username: str = Query(..., description="プレイヤー名")
):
    """
    ゲーム用WebSocketエンドポイント
    
    Args:
        websocket: WebSocket接続
        game_id: ゲームID
        username: プレイヤー名
    """
    await game_manager.connect(websocket, game_id, username)
    
    # 接続完了メッセージを送信
    await game_manager.send_to_player(
        game_id,
        username,
        {
            "type": "connected",
            "message": "ゲームに接続しました",
            "game_id": game_id,
            "player_id": username
        }
    )
    
    # 他のプレイヤーに参加通知
    await game_manager.broadcast_to_game(
        game_id,
        {
            "type": "player_joined",
            "username": username,
            "message": f"{username} がゲームに参加しました"
        },
        exclude_player=username
    )
    
    try:
        while True:
            # クライアントからのメッセージを受信
            data = await websocket.receive_json()
            
            message_type = data.get("type", "")
            
            if message_type == "action":
                # プレイヤーのアクション（fold, check, call, raise, allin）
                action = data.get("action")
                amount = data.get("amount", 0)
                
                logger.info(f"Player {username} performed action: {action} with amount: {amount}")
                
                # TODO: ゲームロジックを実装
                # 現時点では全プレイヤーにブロードキャスト
                await game_manager.broadcast_to_game(
                    game_id,
                    {
                        "type": "player_action",
                        "username": username,
                        "action": action,
                        "amount": amount
                    }
                )
            
            elif message_type == "chat":
                # チャットメッセージ
                message = data.get("message", "")
                await game_manager.broadcast_to_game(
                    game_id,
                    {
                        "type": "chat",
                        "username": username,
                        "message": message
                    }
                )
            
            elif message_type == "get_state":
                # ゲーム状態のリクエスト
                # TODO: 実際のゲーム状態を返す
                await game_manager.send_to_player(
                    game_id,
                    username,
                    {
                        "type": "game_state",
                        "state": {
                            "players": [],
                            "communityCards": [],
                            "pot": 0,
                            "currentPlayerIndex": 0,
                            "phase": "waiting"
                        }
                    }
                )
    
    except WebSocketDisconnect:
        # 接続が切断された場合
        result = game_manager.disconnect(websocket)
        if result:
            game_id, username = result
            logger.info(f"Player {username} disconnected from game {game_id}")
            
            # 切断通知を他のプレイヤーに送信
            await game_manager.broadcast_to_game(
                game_id,
                {
                    "type": "player_left",
                    "username": username,
                    "message": f"{username} がゲームから退出しました"
                }
            )
    
    except Exception as e:
        logger.error(f"Error in game websocket: {e}")
        game_manager.disconnect(websocket)
