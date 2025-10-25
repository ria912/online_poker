"""
WebSocketエンドポイント
ゲーム進行のためのリアルタイム通信
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from typing import Optional
import asyncio
import logging

from .connection_manager import connection_manager
from .serializers import serialize_game_state, create_message
from app.game.services.game_service import game_service
from app.game.services.ai_service import AIService
from app.game.domain.player import Player
from app.game.domain.enum import ActionType, GameStatus
from app.game.domain.action import PlayerAction

logger = logging.getLogger(__name__)
router = APIRouter()

ai_service = AIService()


@router.websocket("/ws/game/{game_id}")
async def game_websocket(
    websocket: WebSocket,
    game_id: str,
    username: str = Query(..., min_length=1, max_length=20)
):
    """
    ゲーム用WebSocketエンドポイント
    
    接続フロー:
    1. ゲームの存在確認
    2. プレイヤー作成と座席配置
    3. WebSocket接続確立
    4. 初期状態送信
    5. メッセージループ開始
    """
    
    # 1. ゲームの存在確認
    game = game_service.get_game_state(game_id)
    if not game:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Game not found")
        logger.warning(f"Connection rejected: game {game_id} not found")
        return
    
    # 2. プレイヤー作成
    import uuid
    player_id = str(uuid.uuid4())
    player = Player(player_id=player_id, name=username, is_ai=False)
    
    # 3. 座席配置
    success = await game_service.setup_single_play_seats(game_id, player)
    if not success:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Failed to setup seats")
        logger.warning(f"Connection rejected: failed to setup seats for {username} in game {game_id}")
        return
    
    # 4. WebSocket接続確立
    await connection_manager.connect(websocket, game_id, player_id)
    
    try:
        # 5. 接続成功メッセージ送信
        await connection_manager.send_personal(
            game_id,
            player_id,
            create_message("connected", {
                "player_id": player_id,
                "game_id": game_id,
                "message": f"Welcome {username}!"
            })
        )
        
        # 6. 初期ゲーム状態を送信
        await broadcast_game_state(game_id)
        
        # 7. メッセージループ
        while True:
            data = await websocket.receive_json()
            await handle_message(game_id, player_id, data)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {username} from game {game_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}", exc_info=True)
    finally:
        # クリーンアップ
        connection_manager.disconnect(websocket)
        
        # プレイヤーをゲームから削除
        game.remove_player_by_id(player_id)
        logger.info(f"Player {username} removed from game {game_id}")


async def handle_message(game_id: str, player_id: str, data: dict) -> None:
    """
    クライアントからのメッセージを処理
    
    Args:
        game_id: ゲームID
        player_id: プレイヤーID
        data: 受信したメッセージデータ
    """
    message_type = data.get("type")
    
    try:
        if message_type == "start_game":
            await handle_start_game(game_id, player_id)
        
        elif message_type == "player_action":
            await handle_player_action(game_id, player_id, data)
        
        elif message_type == "get_state":
            await send_game_state(game_id, player_id)
        
        else:
            logger.warning(f"Unknown message type: {message_type}")
            await connection_manager.send_personal(
                game_id,
                player_id,
                create_message("error", None, f"Unknown message type: {message_type}")
            )
    
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        await connection_manager.send_personal(
            game_id,
            player_id,
            create_message("error", None, str(e))
        )


async def handle_start_game(game_id: str, player_id: str) -> None:
    """
    ゲーム開始処理
    
    Args:
        game_id: ゲームID
        player_id: プレイヤーID
    """
    logger.info(f"Starting game {game_id} by player {player_id}")
    
    success = await game_service.start_game(game_id)
    
    if success:
        await broadcast_game_state(game_id)
        
        # AIのターンをチェック
        await process_ai_turns(game_id)
    else:
        await connection_manager.send_personal(
            game_id,
            player_id,
            create_message("error", None, "Failed to start game. Need at least 2 players.")
        )


async def handle_player_action(game_id: str, player_id: str, data: dict) -> None:
    """
    プレイヤーアクション処理
    
    Args:
        game_id: ゲームID
        player_id: プレイヤーID
        data: アクションデータ
    """
    try:
        action_type_str = data.get("action")
        amount = data.get("amount", 0)
        
        # ActionTypeに変換
        action_type = ActionType(action_type_str.upper())
        
        logger.info(f"Player {player_id} action: {action_type.value} amount: {amount}")
        
        # アクション処理
        success = await game_service.process_player_action(
            game_id,
            player_id,
            action_type,
            amount
        )
        
        if success:
            # 全員に状態をブロードキャスト
            await broadcast_game_state(game_id)
            
            # ゲーム終了チェック
            game = game_service.get_game_state(game_id)
            if game and game.status not in [GameStatus.HAND_COMPLETE, GameStatus.WAITING]:
                # AIのターンを処理
                await process_ai_turns(game_id)
        else:
            await connection_manager.send_personal(
                game_id,
                player_id,
                create_message("error", None, "Invalid action")
            )
    
    except ValueError as e:
        logger.error(f"Invalid action type: {e}")
        await connection_manager.send_personal(
            game_id,
            player_id,
            create_message("error", None, f"Invalid action: {str(e)}")
        )


async def process_ai_turns(game_id: str, max_iterations: int = 10) -> None:
    """
    AIのターンを自動処理
    
    Args:
        game_id: ゲームID
        max_iterations: 最大処理回数（無限ループ防止）
    """
    game = game_service.get_game_state(game_id)
    if not game:
        return
    
    for i in range(max_iterations):
        # 現在のターンがAIかチェック
        if game.current_seat_index is None:
            break
        
        current_seat = game.table.seats[game.current_seat_index]
        
        # AIでない、または座席が空ならループ終了
        if not current_seat.is_occupied or not current_seat.player.is_ai:
            break
        
        # ゲーム終了状態ならループ終了
        if game.status in [GameStatus.HAND_COMPLETE, GameStatus.WAITING]:
            break
        
        # AIアクション決定
        ai_action = ai_service.decide_action(game, current_seat)
        if not ai_action:
            logger.warning(f"AI could not decide action for seat {current_seat.index}")
            break
        
        logger.info(f"AI {current_seat.player.name} action: {ai_action.action_type.value}")
        
        # 少し待つ（リアルっぽく）
        await asyncio.sleep(1.5)
        
        # アクション実行
        success = await game_service.poker_engine.process_action(game, ai_action)
        if not success:
            logger.error(f"AI action failed for {current_seat.player.name}")
            break
        
        # 状態をブロードキャスト
        await broadcast_game_state(game_id)
    
    if i >= max_iterations - 1:
        logger.warning(f"AI turn processing reached max iterations for game {game_id}")


async def send_game_state(game_id: str, player_id: str) -> None:
    """
    特定のプレイヤーにゲーム状態を送信
    
    Args:
        game_id: ゲームID
        player_id: プレイヤーID
    """
    game = game_service.get_game_state(game_id)
    if not game:
        return
    
    state = serialize_game_state(game, player_id)
    await connection_manager.send_personal(
        game_id,
        player_id,
        create_message("game_state", state)
    )


async def broadcast_game_state(game_id: str) -> None:
    """
    全プレイヤーにゲーム状態をブロードキャスト
    
    Args:
        game_id: ゲームID
    """
    game = game_service.get_game_state(game_id)
    if not game:
        return
    
    # 各プレイヤーに個別に送信（ホールカードの表示制御のため）
    connected_players = connection_manager.get_connected_players(game_id)
    
    for player_id in connected_players:
        state = serialize_game_state(game, player_id)
        await connection_manager.send_personal(
            game_id,
            player_id,
            create_message("game_state", state)
        )
