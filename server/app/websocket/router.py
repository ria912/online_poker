"""WebSocketルーター"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
import logging

from .connection_manager import manager
from ..game.services.game_service import game_service
from ..game.domain.player import Player
from ..game.domain.enum import ActionType

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/game/{game_id}/{player_id}")
async def websocket_game_endpoint(websocket: WebSocket, game_id: str, player_id: str):
    """
    ゲーム用WebSocketエンドポイント
    
    接続URL: ws://localhost:8000/ws/game/{game_id}/{player_id}
    
    クライアント → サーバー メッセージ:
    {
        "type": "join_game",
        "player_name": "Alice",
        "buy_in": 10000
    }
    {
        "type": "start_game"
    }
    {
        "type": "player_action",
        "action_type": "CALL",  // FOLD, CHECK, CALL, BET, RAISE, ALL_IN
        "amount": 100  // BET, RAISE時のみ
    }
    {
        "type": "get_state"
    }
    
    サーバー → クライアント メッセージ:
    {
        "type": "connected",
        "game_id": "game_1",
        "player_id": "p1"
    }
    {
        "type": "game_state_update",
        "game_state": {...},
        "your_seat_index": 0,
        "valid_actions": ["FOLD", "CALL", "RAISE"]
    }
    {
        "type": "player_joined",
        "player_id": "p2",
        "player_name": "Bob"
    }
    {
        "type": "game_started"
    }
    {
        "type": "action_result",
        "success": true,
        "message": "Action processed"
    }
    {
        "type": "error",
        "message": "Error message"
    }
    """
    await manager.connect(websocket, game_id, player_id)
    
    try:
        # 接続成功通知
        await manager.send_personal_message(
            {
                "type": "connected",
                "game_id": game_id,
                "player_id": player_id
            },
            game_id,
            player_id
        )
        
        while True:
            # クライアントからのメッセージを受信
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "join_game":
                await handle_join_game(data, game_id, player_id)
            
            elif message_type == "start_game":
                await handle_start_game(game_id, player_id)
            
            elif message_type == "player_action":
                await handle_player_action(data, game_id, player_id)
            
            elif message_type == "get_state":
                await handle_get_state(game_id, player_id)
            
            else:
                await manager.send_personal_message(
                    {
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    },
                    game_id,
                    player_id
                )
    
    except WebSocketDisconnect:
        manager.disconnect(game_id, player_id)
        logger.info(f"Client {player_id} disconnected from game {game_id}")
        
        # 切断を他のプレイヤーに通知
        await manager.broadcast_to_game(
            {
                "type": "player_disconnected",
                "player_id": player_id
            },
            game_id
        )
    
    except Exception as e:
        logger.error(f"WebSocket error for {player_id} in game {game_id}: {e}")
        manager.disconnect(game_id, player_id)


async def handle_join_game(data: Dict[str, Any], game_id: str, player_id: str):
    """ゲーム参加処理"""
    try:
        player_name = data.get("player_name", f"Player_{player_id}")
        buy_in = data.get("buy_in", 10000)
        
        # ゲームが存在しない場合は作成
        game = game_service.get_game_state(game_id)
        if not game:
            await game_service.create_game(game_id, big_blind=100)
        
        # プレイヤー参加
        player = Player(player_id, player_name, is_ai=False)
        success = await game_service.join_game(game_id, player, buy_in)
        
        if success:
            # 参加成功を本人に通知
            await manager.send_personal_message(
                {
                    "type": "join_success",
                    "message": f"Joined game {game_id} successfully"
                },
                game_id,
                player_id
            )
            
            # 他のプレイヤーに新規参加を通知
            await manager.broadcast_to_game(
                {
                    "type": "player_joined",
                    "player_id": player_id,
                    "player_name": player_name
                },
                game_id,
                exclude_player=player_id
            )
            
            # 全員にゲーム状態を送信
            await broadcast_game_state(game_id)
        else:
            await manager.send_personal_message(
                {
                    "type": "error",
                    "message": "Failed to join game (game full or already started)"
                },
                game_id,
                player_id
            )
    
    except Exception as e:
        logger.error(f"Error in handle_join_game: {e}")
        await manager.send_personal_message(
            {
                "type": "error",
                "message": str(e)
            },
            game_id,
            player_id
        )


async def handle_start_game(game_id: str, player_id: str):
    """ゲーム開始処理"""
    try:
        success = await game_service.start_game(game_id)
        
        if success:
            # 全員にゲーム開始を通知
            await manager.broadcast_to_game(
                {
                    "type": "game_started",
                    "message": "Game has started!"
                },
                game_id
            )
            
            # ゲーム状態を送信
            await broadcast_game_state(game_id)
        else:
            await manager.send_personal_message(
                {
                    "type": "error",
                    "message": "Cannot start game (not enough players or already started)"
                },
                game_id,
                player_id
            )
    
    except Exception as e:
        logger.error(f"Error in handle_start_game: {e}")
        await manager.send_personal_message(
            {
                "type": "error",
                "message": str(e)
            },
            game_id,
            player_id
        )


async def handle_player_action(data: Dict[str, Any], game_id: str, player_id: str):
    """プレイヤーアクション処理"""
    try:
        action_type_str = data.get("action_type")
        amount = data.get("amount")
        
        # ActionType に変換
        try:
            action_type = ActionType[action_type_str]
        except KeyError:
            await manager.send_personal_message(
                {
                    "type": "error",
                    "message": f"Invalid action type: {action_type_str}"
                },
                game_id,
                player_id
            )
            return
        
        # アクション実行
        success = await game_service.process_player_action(
            game_id,
            player_id,
            action_type,
            amount
        )
        
        if success:
            # アクション成功を本人に通知
            await manager.send_personal_message(
                {
                    "type": "action_result",
                    "success": True,
                    "message": f"Action {action_type_str} processed"
                },
                game_id,
                player_id
            )
            
            # 全員にゲーム状態を送信
            await broadcast_game_state(game_id)
        else:
            await manager.send_personal_message(
                {
                    "type": "action_result",
                    "success": False,
                    "message": "Invalid action"
                },
                game_id,
                player_id
            )
    
    except Exception as e:
        logger.error(f"Error in handle_player_action: {e}")
        await manager.send_personal_message(
            {
                "type": "error",
                "message": str(e)
            },
            game_id,
            player_id
        )


async def handle_get_state(game_id: str, player_id: str):
    """ゲーム状態取得"""
    try:
        game = game_service.get_game_state(game_id)
        
        if game:
            # プレイヤーの座席インデックスを取得
            player_seat_index = None
            for seat in game.table.seats:
                if seat.is_occupied and seat.player.id == player_id:
                    player_seat_index = seat.index
                    break
            
            # ゲーム状態を送信
            await manager.send_personal_message(
                {
                    "type": "game_state_update",
                    "game_state": serialize_game_state(game),
                    "your_seat_index": player_seat_index,
                    "valid_actions": get_valid_actions(game, player_id)
                },
                game_id,
                player_id
            )
        else:
            await manager.send_personal_message(
                {
                    "type": "error",
                    "message": "Game not found"
                },
                game_id,
                player_id
            )
    
    except Exception as e:
        logger.error(f"Error in handle_get_state: {e}")
        await manager.send_personal_message(
            {
                "type": "error",
                "message": str(e)
            },
            game_id,
            player_id
        )


async def broadcast_game_state(game_id: str):
    """ゲーム状態を全プレイヤーに送信"""
    game = game_service.get_game_state(game_id)
    
    if not game:
        return
    
    connected_players = manager.get_connected_players(game_id)
    
    for player_id in connected_players:
        # プレイヤーの座席インデックスを取得
        player_seat_index = None
        for seat in game.table.seats:
            if seat.is_occupied and seat.player.id == player_id:
                player_seat_index = seat.index
                break
        
        # プレイヤーごとに個別のメッセージを送信（ホールカードは自分のもののみ表示）
        await manager.send_personal_message(
            {
                "type": "game_state_update",
                "game_state": serialize_game_state(game, player_id),
                "your_seat_index": player_seat_index,
                "valid_actions": get_valid_actions(game, player_id),
                "is_your_turn": game.current_seat_index == player_seat_index
            },
            game_id,
            player_id
        )


def serialize_game_state(game, requesting_player_id: str = None) -> Dict[str, Any]:
    """ゲーム状態をJSON化（プレイヤー視点）"""
    seats_data = []
    
    for seat in game.table.seats:
        seat_data = {
            "index": seat.index,
            "is_occupied": seat.is_occupied,
            "stack": seat.stack,
            "bet_in_round": seat.bet_in_round,
            "total_bet_in_hand": seat.total_bet_in_hand,
            "in_hand": seat.in_hand,
            "acted": seat.acted,
        }
        
        if seat.is_occupied:
            seat_data["player"] = {
                "id": seat.player.id,
                "name": seat.player.name,
                "is_ai": seat.player.is_ai
            }
            
            # ホールカードは本人または公開済みの場合のみ表示
            if requesting_player_id == seat.player.id or game.current_round.value in ["SHOWDOWN", "HAND_COMPLETE"]:
                seat_data["hole_cards"] = [str(card) for card in seat.hole_cards]
            else:
                seat_data["hole_cards_count"] = len(seat.hole_cards)
        
        seats_data.append(seat_data)
    
    return {
        "id": game.id,
        "status": game.status.value,
        "current_round": game.current_round.value,
        "dealer_seat_index": game.dealer_seat_index,
        "small_blind_seat_index": game.small_blind_seat_index,
        "big_blind_seat_index": game.big_blind_seat_index,
        "current_seat_index": game.current_seat_index,
        "current_bet": game.current_bet,
        "small_blind": game.small_blind,
        "big_blind": game.big_blind,
        "community_cards": [str(card) for card in game.table.community_cards],
        "total_pot": game.table.total_pot,
        "pots": [
            {
                "amount": pot.amount,
                "eligible_seats": pot.eligible_seats
            }
            for pot in game.table.pots
        ],
        "seats": seats_data,
        "winners": game.winners if hasattr(game, 'winners') else []
    }


def get_valid_actions(game, player_id: str) -> list:
    """プレイヤーの有効なアクションリストを取得"""
    from ..game.services.turn_manager import TurnManager
    
    # 現在のアクタープレイヤーでない場合は空リスト
    if game.current_seat_index is None:
        return []
    
    current_seat = game.table.seats[game.current_seat_index]
    if not current_seat.is_occupied or current_seat.player.id != player_id:
        return []
    
    turn_manager = TurnManager()
    valid_actions = turn_manager.get_valid_actions(game, game.current_seat_index)
    
    return [action.value for action in valid_actions]
