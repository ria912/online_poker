# app/game/services/showdown_service.py
from typing import List, Dict, Any, Optional
from ..domain.game_state import GameState
from ..domain.enum import GameStatus, Round
from ..logic.hand_evaluator import HandEvaluator


class ShowdownService:
    """ショーダウン処理を担当するサービス"""
    
    def __init__(self):
        self.hand_evaluator = HandEvaluator()
    
    def evaluate_showdown(self, game: GameState) -> List[Dict[str, Any]]:
        """
        ショーダウンを評価し、勝者とポット分配を計算
        
        Args:
            game: ゲーム状態
            
        Returns:
            勝者情報のリスト [{"seat_index": int, "player_id": str, "amount": int, "hand_name": str}]
        """
        # コミュニティカードが5枚あるか確認
        if len(game.table.community_cards) != 5:
            return []
        
        # 各プレイヤーのハンドを評価
        in_hand_seats = game.table.in_hand_seats()
        
        for seat in in_hand_seats:
            if len(seat.hole_cards) == 2:
                # ハンド評価値を計算（低いほど強い）
                hand_score = self.hand_evaluator.evaluate_hand(
                    seat.hole_cards,
                    game.table.community_cards
                )
                seat.hand_score = hand_score
                # ショーダウンに参加する座席はカードを見せる
                seat.show_hand = True
        
        # ポット分配を計算（PotManagerを使用）
        from ..logic.pot_manager import PotManager
        distributions = PotManager.calculate_pot_distribution(game)
        
        # 実際にスタックに分配
        for dist in distributions:
            seat_index = dist["seat_index"]
            amount = dist["amount"]
            game.table.seats[seat_index].refund(amount)
        
        # 勝者情報を作成
        winners = []
        for dist in distributions:
            seat_index = dist["seat_index"]
            seat = game.table.seats[seat_index]
            
            # 役名を取得
            hand_name = self.hand_evaluator.get_hand_name(
                seat.hole_cards,
                game.table.community_cards,
                locale="ja"
            )
            
            winners.append({
                "seat_index": seat_index,
                "player_id": seat.player.id if seat.player else "",
                "player_name": seat.player.name if seat.player else "",
                "amount": dist["amount"],
                "pot_type": dist["pot_type"],
                "hand_name": hand_name,
                "hand_score": seat.hand_score,
                "hole_cards": [str(card) for card in seat.hole_cards],
            })
        
        # ゲーム状態を更新
        game.status = GameStatus.HAND_COMPLETE
        
        return winners
    
    def handle_hand_resolution(
        self, 
        game: GameState,
        dealer_service: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        ハンド終了時の処理（フォールドによる終了またはショーダウン）
        
        Args:
            game: ゲーム状態
            
        Returns:
            勝者情報のリスト
        """
        in_hand_seats = game.table.in_hand_seats()
        
        if len(in_hand_seats) == 1:
            winner_seat = in_hand_seats[0]
            total_pot = game.table.total_pot
            
            # 勝者にポット全額を渡す
            winner_seat.refund(total_pot)
            
            # 勝者情報を作成
            winners = [{
                "seat_index": winner_seat.index,
                "player_id": winner_seat.player.id if winner_seat.player else "",
                "player_name": winner_seat.player.name if winner_seat.player else "",
                "amount": total_pot,
                "pot_type": "main",
                "hand_name": "フォールド勝ち",
                "hand_score": 0,
                "hole_cards": [],  # フォールド勝ちの場合はカードを見せない
            }]
            
            # ゲーム状態を更新
            game.status = GameStatus.HAND_COMPLETE
            
            return winners
        
        # コミュニティカードが5枚未満の場合、残りを配る
        while len(game.table.community_cards) < 5:
            if game.current_round == Round.PREFLOP:
                game.current_round = Round.FLOP
                dealer_service.deal_community_cards(game)
            elif game.current_round == Round.FLOP:
                game.current_round = Round.TURN
                dealer_service.deal_community_cards(game)
            elif game.current_round == Round.TURN:
                game.current_round = Round.RIVER
                dealer_service.deal_community_cards(game)
            else:
                break
        
        # ショーダウン評価
        game.current_round = Round.SHOWDOWN
        return self.evaluate_showdown(game)
