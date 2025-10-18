# app/game/domain/game_state.py
from typing import Optional, List, Dict, Any
from .deck import Deck
from .player import Player
from .seat import Seat
from .table import Table
from .action import PlayerAction
from .enum import Round, GameStatus, ActionType, Position
import uuid

class GameState:
    """ゲーム全体の進行状態を管理するクラス"""
    def __init__(self, big_blind: int=100, small_blind: int=50, seat_count: int=3):
        self.id: str = str(uuid.uuid4())
        self.history: list[PlayerAction] = []
        self.status: GameStatus = GameStatus.WAITING
        self.players: List[Player] = []
        self.table: Table = Table(seat_count=seat_count)
        self.current_round: Round = Round.PREFLOP
        
        self.big_blind: int = big_blind
        self.small_blind: int = small_blind

        self.dealer_seat_index: Optional[int] = None
        self.small_blind_seat_index: Optional[int] = None
        self.big_blind_seat_index: Optional[int] = None
        self.current_seat_index: Optional[int] = None
        self.last_aggressive_actor_index: Optional[int] = None # ラウンド終了判定に使用？

        self.current_bet: int = 0       # 現在のベット額
        self.min_raise_amount: int = 0  # 最小レイズ額(総額)
        self.last_raise_delta: int = 0  # 最後のレイズ幅

        self.winners: List[Dict[str, Any]] = []
        self.valid_actions: List[Dict[str, Any]] = []

    def get_player_by_id(self, player_id: str) -> Optional[Player]:
       """player_idからプレイヤーオブジェクトを検索する"""
       for player in self.players:
           if player.id == player_id:
               return player
       return None

    def add_player(self, player: Player):
        """セッションにプレイヤーを追加する"""
        if player not in self.players:
            self.players.append(player)
            try:
                print(f"GameState.add_player: added player id={player.id} name={player.name} total_players={len(self.players)}")
            except Exception:
                pass

    def remove_player_by_id(self, player_id: str):
        """player_idを元にセッションからプレイヤーを削除する"""
        player_to_remove = self.get_player_by_id(player_id)
        if player_to_remove:
            # もしプレイヤーが着席していたら、立たせる
            for seat in self.table.seats:
                if seat.player and seat.player.id == player_to_remove.id:
                    seat.stand_up()
                    break
            try:
                self.players.remove(player_to_remove)
                print(f"GameState.remove_player_by_id: removed player id={player_to_remove.id} t_id={player_id} total_players={len(self.players)}")
            except ValueError:
                print(f"GameState.remove_player_by_id: attempted to remove non-existent player for t_id={player_id}")

    def add_action(self, player_id: str, action_type: ActionType, amount: Optional[int] = None):
        """アクションを履歴に追加する"""
        action = PlayerAction(player_id=player_id, action_type=action_type, amount=amount)
        self.history.append(action)

    def clear_for_new_hand(self):
        """次のハンドのためにゲーム状態をリセットする"""
        self.table.reset_for_new_hand()
        self.history = []
        self.status = GameStatus.WAITING
        self.current_round = Round.PREFLOP

        self.current_seat_index = None
        self.winners = []
        
        self.clear_for_new_round()

    def clear_for_new_round(self):
        """次のベッティングラウンドのために状態をリセットする"""
        self.last_aggressive_actor_index = None
        self.amount_to_call = 0
        self.min_raise_amount = self.big_blind
        self.last_raise_delta = self.big_blind
        self.is_bet_in_round = False