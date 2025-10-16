from typing import List, Dict, Any
from ..models.game_state import GameState
from .hand_evaluator import HandEvaluator

class HandService:
    """ショーダウン処理専門のサービス（カード配布はDealerServiceに移管）"""
    
    def __init__(self):
        self.hand_evaluator = HandEvaluator()
    
    
    def evaluate_showdown(self, game: GameState) -> List[Dict[str, Any]]:
        """ショーダウンでの勝者決定とポット分配"""
        in_hand_seats = [seat for seat in game.table.seats if seat.in_hand]
        
        if len(in_hand_seats) <= 1:
            # 1人以下の場合、その人が勝者
            if in_hand_seats:
                winner = in_hand_seats[0]
                return [{
                    "player_id": winner.player.id,
                    "seat_index": winner.index,
                    "hand_rank": 0,
                    "best_hand": [],
                    "pot_won": game.table.total_pot
                }]
            return []
        
        # 各プレイヤーのハンドを評価
        for seat in in_hand_seats:
            if len(seat.hole_cards) == 2 and len(game.table.community_cards) >= 3:
                hand_rank = self.hand_evaluator.evaluate_hand(
                    seat.hole_cards, 
                    game.table.community_cards
                )
                seat.hand_score = hand_rank
        
        # ポット分配処理（DealerServiceに移管）
        # 簡易実装：最高ハンドが全ポットを獲得
        best_score = min(seat.hand_score for seat in in_hand_seats)
        winners = [seat for seat in in_hand_seats if seat.hand_score == best_score]
        
        total_pot = sum(pot.amount for pot in game.table.pots)
        share_per_winner = total_pot // len(winners)
        remainder = total_pot % len(winners)
        
        results = []
        for i, winner_seat in enumerate(winners):
            share = share_per_winner + (1 if i < remainder else 0)
            results.append({
                "player_id": winner_seat.player.id,
                "seat_index": winner_seat.index,
                "hand_rank": winner_seat.hand_score,
                "best_hand": winner_seat.hole_cards,  # 簡略化
                "pot_won": share
            })
        
        return results