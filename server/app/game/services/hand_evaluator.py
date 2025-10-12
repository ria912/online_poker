"""ハンド評価システム - treysライブラリを使用"""
from typing import List, Tuple, Optional
from treys import Evaluator, Card as TreysCard
from ..domain.deck import Card


class HandEvaluator:
    """ポーカーハンドの評価を行うクラス"""
    
    def __init__(self):
        self.evaluator = Evaluator()
    
    def evaluate_hand(self, hole_cards: List[Card], community_cards: List[Card]) -> int:
        """
        ハンドの強さを評価する
        
        Args:
            hole_cards: プレイヤーのホールカード（2枚）
            community_cards: コミュニティカード（3-5枚）
        
        Returns:
            int: ハンドの評価値（低いほど強い）
        """
        if len(hole_cards) != 2:
            raise ValueError("ホールカードは2枚である必要があります")
        
        if len(community_cards) < 3 or len(community_cards) > 5:
            raise ValueError("コミュニティカードは3-5枚である必要があります")
        
        # CardオブジェクトをTreysの整数表現に変換
        treys_hole = [card.to_treys_int() for card in hole_cards]
        treys_community = [card.to_treys_int() for card in community_cards]
        
        # ハンドを評価
        hand_rank = self.evaluator.evaluate(treys_community, treys_hole)
        return hand_rank
    
    def get_hand_class(self, hole_cards: List[Card], community_cards: List[Card]) -> str:
        """
        ハンドのクラス名を取得する
        
        Returns:
            str: ハンドクラス名（例: "Straight Flush", "Four of a Kind"）
        """
        hand_rank = self.evaluate_hand(hole_cards, community_cards)
        hand_class = self.evaluator.get_rank_class(hand_rank)
        return self.evaluator.class_to_string(hand_class)
    
    def compare_hands(
        self, 
        hand1_hole: List[Card], 
        hand1_community: List[Card],
        hand2_hole: List[Card], 
        hand2_community: List[Card]
    ) -> int:
        """
        2つのハンドを比較する
        
        Returns:
            int: -1 (hand1が勝利), 0 (引き分け), 1 (hand2が勝利)
        """
        rank1 = self.evaluate_hand(hand1_hole, hand1_community)
        rank2 = self.evaluate_hand(hand2_hole, hand2_community)
        
        if rank1 < rank2:  # treysでは低い値が強いハンド
            return -1
        elif rank1 > rank2:
            return 1
        else:
            return 0
    
    def get_best_five_cards(
        self, 
        hole_cards: List[Card], 
        community_cards: List[Card]
    ) -> Tuple[List[Card], int]:
        """
        7枚のカードから最強の5枚を選択する
        
        Returns:
            Tuple[List[Card], int]: (最強の5枚のカード, 評価値)
        """
        all_cards = hole_cards + community_cards
        if len(all_cards) != 7:
            raise ValueError("合計7枚のカードが必要です")
        
        # 全ての5枚の組み合わせを評価
        from itertools import combinations
        
        best_rank = float('inf')
        best_cards = None
        
        for five_cards in combinations(all_cards, 5):
            treys_cards = [card.to_treys_int() for card in five_cards]
            rank = self.evaluator.five(treys_cards)
            
            if rank < best_rank:
                best_rank = rank
                best_cards = list(five_cards)
        
        return best_cards, best_rank
    
    def get_hand_strength_percentage(
        self, 
        hole_cards: List[Card], 
        community_cards: List[Card]
    ) -> float:
        """
        ハンドの強さをパーセンテージで表現する
        
        Returns:
            float: 0.0-1.0の範囲でのハンド強度
        """
        hand_rank = self.evaluate_hand(hole_cards, community_cards)
        
        # treysの評価値を0-1の範囲に正規化
        # 最強ハンド(1) ~ 最弱ハンド(7462)の範囲
        max_rank = 7462  # ハイカードの最弱
        min_rank = 1     # ロイヤルストレートフラッシュ
        
        normalized = 1.0 - ((hand_rank - min_rank) / (max_rank - min_rank))
        return max(0.0, min(1.0, normalized))


class HandRankings:
    """ハンドランキングの定数と説明"""
    
    RANKINGS = {
        1: "ロイヤルストレートフラッシュ",
        2: "ストレートフラッシュ", 
        3: "フォーカード",
        4: "フルハウス",
        5: "フラッシュ",
        6: "ストレート",
        7: "スリーカード",
        8: "ツーペア",
        9: "ワンペア",
        10: "ハイカード"
    }
    
    @classmethod
    def get_ranking_name(cls, rank_class: int) -> str:
        """ランククラスから日本語名を取得"""
        return cls.RANKINGS.get(rank_class, "不明")
    
    @classmethod
    def get_all_rankings(cls) -> dict:
        """全ランキングを取得"""
        return cls.RANKINGS.copy()


# 使用例とテスト用の関数
def example_usage():
    """ハンド評価システムの使用例"""
    from ..domain.deck import Deck
    
    # デッキを作成してカードを配る
    deck = Deck()
    
    # プレイヤー1のハンド
    player1_hole = deck.draw(2)
    
    # プレイヤー2のハンド  
    player2_hole = deck.draw(2)
    
    # コミュニティカード（フロップ、ターン、リバー）
    community = deck.draw(5)
    
    # ハンド評価器を作成
    evaluator = HandEvaluator()
    
    # フロップでの評価
    flop = community[:3]
    print(f"フロップ: {[str(card) for card in flop]}")
    
    player1_class = evaluator.get_hand_class(player1_hole, flop)
    player2_class = evaluator.get_hand_class(player2_hole, flop)
    
    print(f"プレイヤー1: {[str(card) for card in player1_hole]} - {player1_class}")
    print(f"プレイヤー2: {[str(card) for card in player2_hole]} - {player2_class}")
    
    # リバーでの最終評価
    print(f"\nリバー: {[str(card) for card in community]}")
    
    # 最強の5枚を取得
    best1, rank1 = evaluator.get_best_five_cards(player1_hole, community)
    best2, rank2 = evaluator.get_best_five_cards(player2_hole, community)
    
    print(f"プレイヤー1最強5枚: {[str(card) for card in best1]}")
    print(f"プレイヤー2最強5枚: {[str(card) for card in best2]}")
    
    # 勝者を決定
    result = evaluator.compare_hands(player1_hole, community, player2_hole, community)
    if result == -1:
        print("プレイヤー1の勝利！")
    elif result == 1:
        print("プレイヤー2の勝利！")
    else:
        print("引き分け！")


if __name__ == "__main__":
    example_usage()