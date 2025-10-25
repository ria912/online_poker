"""AIプレイヤーのアクション決定ロジック"""
from typing import Optional
from ..domain.game_state import GameState
from ..domain.action import PlayerAction
from ..domain.seat import Seat
from ..domain.enum import ActionType


class AIService:
    """AIプレイヤーのアクション決定を行うサービス"""

    def decide_action(self, game: GameState, seat: Seat) -> Optional[PlayerAction]:
        """
        AIのアクション決定ロジック
        
        戦略:
        1. チェックできるならチェック
        2. コールできるならコール（スタックの50%まで）
        3. それ以外はフォールド
        
        Args:
            game: ゲーム状態
            seat: AIプレイヤーの座席
            
        Returns:
            PlayerAction: 決定されたアクション
        """
        if not seat or not seat.is_occupied or not seat.player:
            return None
        
        player_id = seat.player.id
        call_amount = game.current_bet - seat.bet_in_round
        
        # チェックが可能な場合はチェック
        if self._can_check(seat, game.current_bet):
            return PlayerAction(
                player_id=player_id,
                action_type=ActionType.CHECK,
                amount=0
            )
        
        # コールが可能で、スタックの50%以下ならコール
        if self._can_call(seat, call_amount):
            # スタックの50%を超えるコールは避ける（保守的な戦略）
            if call_amount <= seat.stack * 0.5:
                return PlayerAction(
                    player_id=player_id,
                    action_type=ActionType.CALL,
                    amount=call_amount
                )
        
        # それ以外はフォールド
        return PlayerAction(
            player_id=player_id,
            action_type=ActionType.FOLD,
            amount=0
        )

    def _can_call(self, seat: Seat, call_amount: int) -> bool:
        """
        コールが可能かチェック
        
        Args:
            seat: プレイヤーの座席
            call_amount: コールに必要な金額
            
        Returns:
            bool: コール可能ならTrue
        """
        # コール額が0より大きく、スタックが足りる場合
        if call_amount > 0 and seat.stack >= call_amount:
            return True
        
        # オールインの場合もコール扱い
        if call_amount > 0 and seat.stack > 0 and seat.stack < call_amount:
            return True
        
        return False

    def _can_check(self, seat: Seat, current_bet: int) -> bool:
        """
        チェックが可能かチェック
        
        Args:
            seat: プレイヤーの座席
            current_bet: 現在のベット額
            
        Returns:
            bool: チェック可能ならTrue
        """
        # 自分のベット額が現在のベット額と同じ場合のみチェック可能
        return seat.bet_in_round == current_bet

    def should_ai_act(self, game: GameState, player_id: str) -> bool:
        """
        指定されたプレイヤーがAIで、かつアクションすべきタイミングかチェック
        
        Args:
            game: ゲーム状態
            player_id: プレイヤーID
            
        Returns:
            bool: AIがアクションすべきならTrue
        """
        # プレイヤーを検索
        seat = self._find_player_seat(game, player_id)
        if not seat or not seat.is_occupied or not seat.player:
            return False
        
        # AIプレイヤーかチェック（is_aiフラグで判定）
        if not seat.player.is_ai:
            return False
        
        # 現在のターンがこのプレイヤーかチェック
        if game.current_seat_index is None:
            return False
        
        current_seat = game.table.seats[game.current_seat_index]
        return current_seat == seat and seat.is_active

    def _find_player_seat(self, game: GameState, player_id: str) -> Optional[Seat]:
        """
        プレイヤーIDから座席を検索
        
        Args:
            game: ゲーム状態
            player_id: プレイヤーID
            
        Returns:
            Seat: 見つかった座席、見つからない場合はNone
        """
        for seat in game.table.seats:
            if seat.is_occupied and seat.player and seat.player.id == player_id:
                return seat
        return None
