from typing import List, Dict, Any
from ..domain.game_state import GameState
from .hand_evaluator import HandEvaluator

class HandService:
    """ショーダウン処理専門のサービス（カード配布はDealerServiceに移管）"""
    
    def __init__(self):
        self.hand_evaluator = HandEvaluator()
    
    
    def evaluate_hands_for_showdown(self, game: GameState) -> None:
        """ショーダウン対象者のハンドを評価し、hand_scoreを設定する（分配はDealerServiceへ）"""
        in_hand_seats = [seat for seat in game.table.seats if seat.in_hand]
        for seat in in_hand_seats:
            if len(seat.hole_cards) == 2 and len(game.table.community_cards) >= 3:
                hand_rank = self.hand_evaluator.evaluate_hand(
                    seat.hole_cards,
                    game.table.community_cards
                )
                seat.hand_score = hand_rank