from typing import Optional, List
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
            bb_seat_index = game.big_blind_seat_index
            if bb_seat_index is not None:
                # BBの次のアクティブプレイヤーを探す
                next_active = self._get_next_active_seat_index(game, bb_seat_index)
                game.current_seat_index = next_active
        else:
            btn_index = game.dealer_seat_index
            if btn_index is not None:
                # ボタンの次のアクティブプレイヤーを探す
                next_active = self._get_next_active_seat_index(game, btn_index)
                game.current_seat_index = next_active
    
    def advance_to_next_actor(self, game: GameState) -> bool:
        """次のアクターに進める"""
        next_seat_index = self.get_next_actionable_seat_index(game)
        
        if next_seat_index is not None:
            game.current_seat_index = next_seat_index
            return True
        else:
            # ベッティングラウンド終了
            return False

    def _get_next_active_seat_index(self, game: GameState, current_index: int) -> Optional[int]:
        """次のアクティブな座席インデックスを取得"""
        for i in range(1, len(game.table.seats)):
            next_index = (current_index + i) % len(game.table.seats)
            if game.table.seats[next_index].is_active:
                return next_index
        return None
    
    def get_valid_actions(self, game: GameState, seat_index: int) -> List[ActionType]:
        """座席インデックスベースで有効なアクションリストを取得"""
        if seat_index is None:
            seat_index = game.current_seat_index

        if not (0 <= seat_index < len(game.table.seats)):
            return []
        
        seat = game.table.seats[seat_index]
        if not seat.is_active:
            return []

        if game.current_seat_index != seat_index:
            return []
        
        valid_actions: List[ActionType] = []
        # チェック/コール/フォールド
        call_amount = game.current_bet - seat.bet_in_round
        if call_amount == 0:
            valid_actions.append(ActionType.CHECK)
        elif call_amount > 0:
            valid_actions.append(ActionType.CALL)
            valid_actions.append(ActionType.FOLD)
        
        # ベット/レイズ
        if game.current_bet == 0:
            valid_actions.append(ActionType.BET)
        elif seat.stack + seat.bet_in_round > game.current_bet:
            valid_actions.append(ActionType.RAISE)

        return valid_actions
    
    def get_valid_actions_for_player(self, game: GameState, player_id: str) -> List[ActionType]:
        """プレイヤーIDベースで有効なアクションリストを取得"""
        seat = self._find_player_seat(game, player_id)
        if not seat:
            return []
        
        return self.get_valid_actions(game, seat.index)
    
    def _find_player_seat(self, game: GameState, player_id: str) -> Optional[Seat]:
        """プレイヤーIDから座席を検索"""
        for seat in game.table.seats:
            if seat.is_occupied and seat.player.id == player_id:
                return seat
        return None