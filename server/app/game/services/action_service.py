from ..domain.game_state import GameState
from ..domain.action import PlayerAction
from ..domain.seat import Seat
from ..domain.enum import ActionType, SeatStatus

class ActionService:
    """アクション関連のビジネスロジック"""

    async def execute_action(self, game: GameState, action: PlayerAction) -> bool:
        """アクションを実行"""
        seat = self._find_player_seat(game, action.player_id)
        if not seat:
            return False
        if game.current_seat_index is None:
            return False
        if game.table.seats[game.current_seat_index] != seat:
            return False

        if action.action_type == ActionType.FOLD:
            seat.status = SeatStatus.FOLDED
            seat.last_action = ActionType.FOLD
            seat.acted = True

        elif action.action_type == ActionType.CHECK:
            seat.last_action = ActionType.CHECK
            seat.acted = True

        elif action.action_type == ActionType.CALL:
            call_amount = game.current_bet - seat.bet_in_round
            seat.last_action = ActionType.CALL
            seat.pay(call_amount)
            seat.acted = True

        elif action.action_type == ActionType.BET:
            if action.amount and action.amount > 0:
                seat.last_action = ActionType.BET
                seat.pay(action.amount)
                seat.acted = True
                
                # 現在のベット額とアグレッサー更新
                game.current_bet = seat.bet_in_round
                game.last_aggressive_actor_index = seat.index
                
                if action.amount > game.last_raise_delta:
                    game.last_raise_delta = action.amount
                
                # ベットもアグレッシブアクションなので他プレイヤーをリセット
                self._reset_acted_flags_after_raise(game, seat.index)

        elif action.action_type == ActionType.RAISE:
            if action.amount and action.amount > game.current_bet:
                total_bet = action.amount
                raise_amount = total_bet - seat.bet_in_round
                game.current_bet = total_bet
                game.last_aggressive_actor_index = seat.index
                seat.last_action = ActionType.RAISE
                seat.pay(raise_amount)
                seat.acted = True
                if raise_amount > game.last_raise_delta:
                    game.last_raise_delta = raise_amount
                    self._reset_acted_flags_after_raise(game, seat.index)
                
        if seat.stack == 0:
            seat.status = SeatStatus.ALL_IN
        
        return True

    def is_valid_action(self, game: GameState, action: PlayerAction) -> bool:
        """アクションが有効かチェック"""
        seat = self._find_player_seat(game, action.player_id)
        if not seat or not seat.is_active:
            return False
        
        # アクション固有の検証
        if action.action_type == ActionType.FOLD:
            return True
        
        elif action.action_type == ActionType.CALL:
            call_amount = game.current_bet - seat.bet_in_round
            return call_amount > 0 and seat.stack >= call_amount
        
        elif action.action_type == ActionType.CHECK:
            # ベット額が合っている場合のみチェック可能
            return seat.bet_in_round >= game.current_bet
        
        elif action.action_type == ActionType.BET:
            if not action.amount or action.amount <= 0:
                return False
            if game.current_bet > 0:
                return False  # 既にベットがある場合はBET不可
            return seat.stack >= action.amount
        
        elif action.action_type == ActionType.RAISE:
            if not action.amount or action.amount <= game.current_bet:
                return False
            min_raise = game.current_bet + game.big_blind
            needed = action.amount - seat.bet_in_round
            return seat.stack >= needed and action.amount >= min_raise
        
        # デフォルトで拒否
        return False

    def _find_player_seat(self, game: GameState, player_id: str):
        """プレイヤーIDから座席を検索"""
        for seat in game.table.seats:
            if seat.is_occupied and seat.player.id == player_id:
                return seat
        return None

    def _reset_acted_flags_after_raise(self, game: GameState, raiser_seat_index: int) -> None:
        """レイズ後に他のプレイヤーの行動フラグをリセット"""
        for seat in game.table.seats:
            if seat.is_active and seat.index != raiser_seat_index:
                seat.acted = False