from ..domain.game_state import GameState
from ..domain.action import PlayerAction
from ..domain.seat import Seat
from ..domain.enum import ActionType, SeatStatus

class ActionService:
    """アクション関連のビジネスロジック"""

    async def execute_action(self, game: GameState, action: PlayerAction) -> bool:
        """アクションを適用"""
        seat = self._find_player_seat(game, action.player_id)
        if not seat:
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
            if action.amount > game.current_bet:
                bet_amount = seat.pay(action.amount)
                seat.last_action = ActionType.BET
                seat.acted = True
                if bet_amount >= game.big_blind:
                    game.last_raise_delta = bet_amount
                    self._reset_acted_flags_after_raise(game, seat.index)


        elif action.action_type == ActionType.RAISE:
            if action.amount > game.current_bet:
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
        if action.action_type == ActionType.CALL:
            return seat.stack > 0
        elif action.action_type == ActionType.CHECK:
            # ベット額が合っている場合のみチェック可能
            return seat.bet_in_round == game.current_bet
        elif action.action_type == ActionType.BET:
            if not action.amount:
                return False
            # 既にベットがある場合、ベット不可
            if game.current_bet > 0:
                return False
            return action.amount <= seat.stack and action.amount > 0
        elif action.action_type == ActionType.RAISE:
            if not action.amount:
                return False
            # リオープンされていない場合、レイズ不可
            if seat.acted:
                return False
            return action.amount > game.current_bet and action.amount <= (seat.stack + seat.bet_in_round)

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