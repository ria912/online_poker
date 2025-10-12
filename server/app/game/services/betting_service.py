from ..domain.game_state import GameState
from ..domain.action import Action
from ..domain.seat import Seat
from ..domain.enum import ActionType, SeatStatus

class BettingService:
    """ベッティング関連のビジネスロジック"""
    
    async def execute_action(self, game: GameState, action: Action) -> bool:
        """アクションを実行"""
        seat = self._find_player_seat(game, action.player_id)
        if not seat:
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
        elif action.action_type == ActionType.RAISE:
            if action.amount:
                total_bet = action.amount
                raise_amount = total_bet - seat.bet_in_round
                game.current_bet = total_bet
                game.last_aggressive_actor_index = seat.index
                seat.last_action = ActionType.RAISE
                seat.pay(raise_amount)
                
                # レイズがあった場合、他のプレイヤーの行動フラグをリセット
                self._reset_acted_flags_after_raise(game, seat.index)
                
        elif action.action_type == ActionType.ALL_IN:
            old_bet = seat.bet_in_round
            seat.pay(seat.current_stack)
            if seat.bet_in_round > game.current_bet:
                game.current_bet = seat.bet_in_round
                game.last_aggressive_actor_index = seat.index
                # オールインでレイズになった場合、他のプレイヤーの行動フラグをリセット
                if seat.bet_in_round > old_bet:
                    self._reset_acted_flags_after_raise(game, seat.index)
            seat.last_action = ActionType.ALL_IN
        
        return True
    
    def is_valid_action(self, game: GameState, action: Action) -> bool:
        """アクションが有効かチェック"""
        seat = self._find_player_seat(game, action.player_id)
        if not seat or not seat.is_active:
            return False
        
        # アクション固有の検証
        if action.action_type == ActionType.CALL:
            call_amount = game.current_bet - seat.bet_in_round
            return call_amount > 0 and seat.can_pay(call_amount)
        elif action.action_type == ActionType.CHECK:
            # ベット額が合っている場合のみチェック可能
            return seat.bet_in_round == game.current_bet
        elif action.action_type == ActionType.RAISE:
            if not action.amount:
                return False
            min_raise = game.current_bet + game.big_blind
            return (action.amount >= min_raise and 
                   seat.can_pay(action.amount - seat.bet_in_round))
        
        return True
    
    def is_betting_round_complete(self, game: GameState) -> bool:
        """ベッティングラウンドが完了したかチェック（BBオプション考慮なし）"""
        active_seats = [seat for seat in game.table.seats if seat.is_active]
        
        if len(active_seats) <= 1:
            return True
        
        # 全プレイヤーが行動済みで同額ベットしているかチェック
        for seat in active_seats:
            if not seat.acted:
                return False
            if seat.bet_in_round != game.current_bet and seat.status != SeatStatus.ALL_IN:
                return False
        
        return True
    
    def _find_player_seat(self, game: GameState, player_id: str):
        """プレイヤーIDから座席を検索"""
        for seat in game.table.seats:
            if seat.is_occupied and seat.player and seat.player.id == player_id:
                return seat
        return None

    def _reset_acted_flags_after_raise(self, game: GameState, raiser_seat_index: int) -> None:
        """レイズ後に他のプレイヤーの行動フラグをリセット"""
        for seat in game.table.seats:
            if (seat.is_active and 
                seat.index != raiser_seat_index and 
                seat.status != SeatStatus.ALL_IN):
                seat.acted = False