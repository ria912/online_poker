"""ハンド評価（最小実装） - treys Evaluator を使用"""
from typing import List
from treys import Evaluator
from ..domain.deck import Card


class HandEvaluator:
    """ハンド強度の評価のみを提供する最小API"""

    def __init__(self) -> None:
        self.evaluator = Evaluator()
        # treys の hand class (1=最強, 9=最弱) を日本語名にマッピング
        self._JA_HAND_NAMES = {
            1: "ストレートフラッシュ",
            2: "フォーカード",
            3: "フルハウス",
            4: "フラッシュ",
            5: "ストレート",
            6: "スリーカード",
            7: "ツーペア",
            8: "ワンペア",
            9: "ハイカード",
        }

    def evaluate_hand(self, hole_cards: List[Card], community_cards: List[Card]) -> int:
        """ハンドの評価値（低いほど強い）を返す"""
        if len(hole_cards) != 2:
            raise ValueError("ホールカードは2枚である必要があります")
        if not (3 <= len(community_cards) <= 5):
            raise ValueError("コミュニティカードは3-5枚である必要があります")

        treys_hole = [card.to_treys_int() for card in hole_cards]
        treys_community = [card.to_treys_int() for card in community_cards]
        return self.evaluator.evaluate(treys_community, treys_hole)

    def get_hand_name(self, hole_cards: List[Card], community_cards: List[Card], locale: str = "ja") -> str:
        """
        役名を返す。
        locale="ja" で日本語、その他は treys の英語表記を返却。
        """
        hand_rank = self.evaluate_hand(hole_cards, community_cards)
        cls = self.evaluator.get_rank_class(hand_rank)  # 1..9（小さいほど強い）
        if locale.lower() == "ja":
            return self._JA_HAND_NAMES.get(cls, "不明")
        # 英語名称（例: "Straight Flush"）
        return self.evaluator.class_to_string(cls)