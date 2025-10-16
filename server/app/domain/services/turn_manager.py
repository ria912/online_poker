from typing import Optional, List
from ..models.game_state import GameState
from ..models.seat import Seat
from ..models.enum import SeatStatus, Round, ActionType

class TurnManager:
    """ターン管理とBBオプションを考慮したロジック"""
    
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
    
    def is_betting_round_complete(self, game: GameState) -> bool:
        """ベッティングラウンドが完了しているかどうかを判定"""
        active_seats = [seat for seat in game.table.seats if seat.is_active]
        
        # アクティブプレイヤーが1人以下の場合、ラウンド終了
        if len(active_seats) <= 1:
            return True
        
        # BBオプションのチェック
        if self._has_pending_bb_option(game):
            return False
        
        # 全員が以下の条件を満たしている場合、ラウンド終了
        # 1. 行動済み (acted = True)
        # 2. 現在のベット額と同額をベット済み
        for seat in active_seats:
            if not seat.acted:
                return False
            if seat.bet_in_round != game.current_bet:
                return False
        
        return True
    
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
        # 全座席の行動フラグをリセット
        for seat in game.table.seats:
            if seat.is_occupied:
                seat.acted = False
                seat.bet_in_round = 0
        
        # ベット状態をリセット
        game.current_bet = 0
        game.last_aggressive_actor_index = None
    
    def _set_first_actor_preflop(self, game: GameState) -> None:
        """プリフロップの最初のアクターを設定（UTG）"""
        bb_seat_index = self._find_big_blind_seat_index(game)
        if bb_seat_index is not None:
            # BBの次のアクティブプレイヤーを探す
            next_active = self._get_next_active_seat_index(game, bb_seat_index)
            game.current_seat_index = next_active
    
    def _set_first_actor_postflop(self, game: GameState) -> None:
        """ポストフロップの最初のアクターを設定（SBまたは最初のアクティブプレイヤー）"""
        sb_seat_index = self._find_small_blind_seat_index(game)
        if sb_seat_index is not None:
            sb_seat = game.table.seats[sb_seat_index]
            if sb_seat.is_active:
                game.current_seat_index = sb_seat_index
            else:
                # SBがアクティブでない場合、次のアクティブプレイヤー
                game.current_seat_index = self._get_next_active_seat_index(game, sb_seat_index)
        else:
            # SBが見つからない場合、最初のアクティブプレイヤー
            for seat in game.table.seats:
                if seat.is_active:
                    game.current_seat_index = seat.index
                    break
    
    def _find_big_blind_seat_index(self, game: GameState) -> Optional[int]:
        """ビッグブラインドの座席インデックスを取得"""
        if game.big_blind_seat_index is not None:
            return game.big_blind_seat_index
        
        # 簡略化：ディーラーから2つ左の座席をBBとする
        if game.dealer_seat_index is not None:
            return (game.dealer_seat_index + 2) % len(game.table.seats)
        
        # デフォルト：2番目のアクティブプレイヤー
        active_seats = [seat for seat in game.table.seats if seat.is_active]
        return active_seats[1].index if len(active_seats) >= 2 else None
    
    def _find_small_blind_seat_index(self, game: GameState) -> Optional[int]:
        """スモールブラインドの座席インデックスを取得"""
        if game.small_blind_seat_index is not None:
            return game.small_blind_seat_index
        
        # 簡略化：ディーラーから1つ左の座席をSBとする
        if game.dealer_seat_index is not None:
            return (game.dealer_seat_index + 1) % len(game.table.seats)
        
        # デフォルト：最初のアクティブプレイヤー
        active_seats = [seat for seat in game.table.seats if seat.is_active]
        return active_seats[0].index if len(active_seats) >= 1 else None
    
    def _is_big_blind_seat(self, game: GameState, seat_index: int) -> bool:
        """指定した座席がビッグブラインドかどうか"""
        bb_seat_index = self._find_big_blind_seat_index(game)
        return bb_seat_index == seat_index
    
    def _get_next_active_seat_index(self, game: GameState, current_index: int) -> Optional[int]:
        """次のアクティブな座席インデックスを取得"""
        for i in range(1, len(game.table.seats)):
            next_index = (current_index + i) % len(game.table.seats)
            if game.table.seats[next_index].is_active:
                return next_index
        return None
    
    def get_valid_actions_for_player(self, game: GameState, player_id: str) -> List[ActionType]:
        """プレイヤーの有効なアクションリストを取得"""
        seat = self._find_player_seat(game, player_id)
        if not seat or not seat.is_active:
            return []
        
        # 現在のターンでない場合
        if game.current_seat_index != seat.index:
            return []
        
        valid_actions = []
        
        # フォールドは常に可能
        valid_actions.append(ActionType.FOLD)
        
        # コール/チェックの判定
        call_amount = game.current_bet - seat.bet_in_round
        if call_amount == 0:
            # チェック可能
            valid_actions.append(ActionType.CHECK)
        elif seat.can_pay(call_amount):
            # コール可能
            valid_actions.append(ActionType.CALL)
        
        # レイズの判定
        min_raise = game.current_bet + game.big_blind
        if seat.can_pay(min_raise - seat.bet_in_round):
            valid_actions.append(ActionType.RAISE)
        
        # オールイン可能
        if seat.current_stack > 0:
            valid_actions.append(ActionType.ALL_IN)
        
        return valid_actions
    
    def _find_player_seat(self, game: GameState, player_id: str) -> Optional[Seat]:
        """プレイヤーIDから座席を検索"""
        for seat in game.table.seats:
            if seat.is_occupied and seat.player and seat.player.id == player_id:
                return seat
        return None