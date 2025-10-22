from typing import Optional, List, Dict, Any
from ..domain.game_state import GameState
from ..domain.seat import Seat
from ..domain.enum import SeatStatus, Round, ActionType

class TurnManager:
    """ターン管理ロジック"""
    
    def __init__(self):
        pass
    
    def get_next_actionable_seat_index(self, game: GameState) -> Optional[int]:
        """次のアクション可能な座席のインデックスを取得する"""
        if game.current_seat_index is None:
            return None
        
        seats_count = len(game.table.seats)
        seats_checked = 0
        
        for i in range(1, seats_count + 1):
            index = (game.current_seat_index + i) % seats_count
            seat = game.table.seats[index]
            seats_checked += 1
            
            # アクティブな座席のみが対象
            if not seat.is_active:
                continue

            # 通常のアクション判定
            if not seat.acted or seat.bet_in_round < game.current_bet:
                return index
            
            # 全座席をチェックした場合は終了
            if seats_checked >= seats_count:
                break
        
        return None
    
    def set_first_actor_for_round(self, game: GameState) -> None:
        """ラウンド開始時の最初のアクションプレイヤーを設定"""
        if game.current_round == Round.PREFLOP:
            self._set_first_actor_preflop(game)
        else:
            self._set_first_actor_postflop(game)
    
    def advance_to_next_actor(self, game: GameState) -> bool:
        """次のアクターに進める"""
        next_seat_index = self.get_next_actionable_seat_index(game)
        
        if next_seat_index is not None:
            game.current_seat_index = next_seat_index
            return True
        else:
            # ベッティングラウンド終了
            return False
    
    def reset_for_new_round(self, game: GameState) -> None:
        """新しいベッティングラウンドのためにターン状態をリセット"""
        game.table.reset_for_new_round()
        game.current_bet = 0
        game.last_aggressive_actor_index = None
    
    def _set_first_actor_preflop(self, game: GameState) -> None:
        """プリフロップの最初のアクターを設定（UTG）"""
        bb_seat_index = game.big_blind_seat_index
        if bb_seat_index is not None:
            # BBの次のアクティブプレイヤーを探す
            next_active = self._get_next_active_seat_index(game, bb_seat_index)
            game.current_seat_index = next_active
    
    def _set_first_actor_postflop(self, game: GameState) -> None:
        """ポストフロップの最初のアクターを設定（SBまたは最初のアクティブプレイヤー）"""
        btn_index = game.dealer_seat_index
        if btn_index is not None:
            # ボタンの次のアクティブプレイヤーを探す
            next_active = self._get_next_active_seat_index(game, btn_index)
            game.current_seat_index = next_active
    
    def _get_next_active_seat_index(self, game: GameState, current_index: int) -> Optional[int]:
        """次のアクティブな座席インデックスを取得"""
        for i in range(1, len(game.table.seats)):
            next_index = (current_index + i) % len(game.table.seats)
            if game.table.seats[next_index].is_active:
                return next_index
        return None
    
    def get_valid_actions_for_player(self, game: GameState, player_id: str) -> List[Dict[str, Any]]:
        """
        プレイヤーの有効なアクションリストを取得(リッチな情報を含む)
        返り値: [{"type": ActionType, "amount"?: int, "min_amount"?: int, "max_amount"?: int}]
        """
        seat = game.table.get_seat_by_player_id(player_id)
        if not seat or not seat.is_active:
            return []
        
        # 現在のターンでない場合
        if game.current_seat_index != seat.index:
            return []
        
        valid_actions: List[Dict[str, Any]] = []
        
        # フォールドは常に可能
        valid_actions.append({"type": ActionType.FOLD})

        # コール/チェック
        call_amount = game.current_bet - seat.bet_in_round
        if call_amount == 0:
            valid_actions.append({"type": ActionType.CHECK})
        elif seat.stack >= call_amount:
            # CALLに必要な額を明記
            valid_actions.append({"type": ActionType.CALL, "amount": call_amount})
        
        # ベット/レイズ
        if game.current_bet == 0:
            # BETの最小・最大額を明記
            min_bet = game.big_blind
            max_bet = seat.stack
            if max_bet >= min_bet:
                valid_actions.append({
                    "type": ActionType.BET, 
                    "min_amount": min_bet, 
                    "max_amount": max_bet
                })
        else:
            # RAISEの最小・最大額を明記
            min_raise_amount = game.current_bet + max(game.last_raise_delta, game.big_blind)
            available_to_raise = seat.stack + seat.bet_in_round
            if available_to_raise >= min_raise_amount:
                valid_actions.append({
                    "type": ActionType.RAISE, 
                    "min_amount": min_raise_amount, 
                    "max_amount": available_to_raise
                })

        return valid_actions