"""
ゲーム状態のシリアライズ
GameStateをJSON形式に変換してクライアントに送信
"""
from typing import Dict, Any, Optional
from app.game.domain.game_state import GameState
from app.game.domain.seat import Seat
from app.game.domain.deck import Card


def serialize_card(card: Card) -> Dict[str, str]:
    """カードをシリアライズ"""
    return {
        "rank": card.rank,
        "suit": card.suit
    }


def serialize_seat(seat: Seat, viewing_player_id: Optional[str] = None) -> Dict[str, Any]:
    """
    座席をシリアライズ
    
    Args:
        seat: 座席オブジェクト
        viewing_player_id: 閲覧者のプレイヤーID（ホールカードの表示制御用）
    """
    if not seat.is_occupied:
        return {
            "index": seat.index,
            "player": None,
            "stack": 0,
            "status": "EMPTY",
            "bet_in_round": 0,
            "bet_in_hand": 0,
            "hole_cards": [],
            "last_action": None
        }
    
    # ホールカードの表示判定
    # 自分のカード、またはショーダウン時に表示
    show_cards = (viewing_player_id == seat.player.id) or seat.show_hand
    
    return {
        "index": seat.index,
        "player": {
            "id": seat.player.id,
            "name": seat.player.name,
            "is_ai": seat.player.is_ai
        },
        "stack": seat.stack,
        "status": seat.status.value,
        "bet_in_round": seat.bet_in_round,
        "bet_in_hand": seat.bet_in_hand,
        "hole_cards": [serialize_card(card) for card in seat.hole_cards] if show_cards else [],
        "last_action": seat.last_action.value if seat.last_action else None,
        "position": seat.position.value if seat.position else None
    }


def serialize_game_state(game: GameState, viewing_player_id: Optional[str] = None) -> Dict[str, Any]:
    """
    ゲーム状態全体をシリアライズ
    
    Args:
        game: ゲーム状態
        viewing_player_id: 閲覧者のプレイヤーID
    """
    return {
        "game_id": game.id,
        "status": game.status.value,
        "current_round": game.current_round.value,
        "current_seat_index": game.current_seat_index,
        "current_bet": game.current_bet,
        "small_blind": game.small_blind,
        "big_blind": game.big_blind,
        "dealer_seat_index": game.dealer_seat_index,
        "seats": [serialize_seat(seat, viewing_player_id) for seat in game.table.seats],
        "community_cards": [serialize_card(card) for card in game.table.community_cards],
        "pots": [
            {
                "amount": pot.amount,
                "eligible_seats": pot.eligible_seats
            }
            for pot in game.table.pots
        ],
        "winners": game.winners,
        "valid_actions": game.valid_actions
    }


def create_message(message_type: str, data: Any, error: Optional[str] = None) -> Dict[str, Any]:
    """
    標準的なメッセージフォーマットを作成
    
    Args:
        message_type: メッセージタイプ
        data: データペイロード
        error: エラーメッセージ（オプション）
    """
    message = {
        "type": message_type,
        "data": data
    }
    
    if error:
        message["error"] = error
    
    return message
