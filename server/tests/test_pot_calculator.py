# tests/test_pot_calculator.py
"""
ポット計算ロジックのテスト

このテストは、ドメインロジックが正しく動作することを検証します。
GameStateに依存せず、純粋な計算ロジックのみをテストします。
"""
import pytest
from app.game.domain.pot_calculator import PotCalculator, PotDistributor
from app.game.domain.table import Pot
from app.game.domain.seat import Seat
from app.game.domain.player import Player


class TestPotCalculator:
    """PotCalculator クラスのテスト"""
    
    def test_create_pots_no_all_in_single_round(self):
        """オールインなしの場合、メインポットに全額が追加される"""
        bet_contributions = {0: 100, 1: 100, 2: 100}
        all_in_seats = []
        existing_pots = []
        
        pots = PotCalculator.create_pots_from_bets(
            bet_contributions, all_in_seats, existing_pots
        )
        
        assert len(pots) == 1
        assert pots[0].amount == 300
        assert set(pots[0].eligible_seats) == {0, 1, 2}
    
    def test_create_pots_no_all_in_multiple_rounds(self):
        """複数ラウンドでオールインなしの場合、メインポットに累積される"""
        # 1ラウンド目
        bet_contributions_1 = {0: 50, 1: 50, 2: 50}
        pots = PotCalculator.create_pots_from_bets(
            bet_contributions_1, [], []
        )
        assert pots[0].amount == 150
        
        # 2ラウンド目
        bet_contributions_2 = {0: 100, 1: 100, 2: 100}
        pots = PotCalculator.create_pots_from_bets(
            bet_contributions_2, [], pots
        )
        assert len(pots) == 1
        assert pots[0].amount == 450  # 150 + 300
    
    def test_create_pots_single_all_in(self):
        """1人がオールインの場合、サイドポットが作成される"""
        # Player 0: 100 (all-in), Player 1: 200, Player 2: 200
        bet_contributions = {0: 100, 1: 200, 2: 200}
        all_in_seats = [0]
        existing_pots = []
        
        pots = PotCalculator.create_pots_from_bets(
            bet_contributions, all_in_seats, existing_pots
        )
        
        # メインポット: 100 * 3 = 300 (全員が対象)
        # サイドポット: 100 * 2 = 200 (Player 1, 2が対象)
        assert len(pots) == 2
        assert pots[0].amount == 300
        assert set(pots[0].eligible_seats) == {0, 1, 2}
        assert pots[1].amount == 200
        assert set(pots[1].eligible_seats) == {1, 2}
    
    def test_create_pots_multiple_all_in(self):
        """複数人がオールインの場合、複数のサイドポットが作成される"""
        # Player 0: 100 (all-in), Player 1: 200 (all-in), Player 2: 300
        bet_contributions = {0: 100, 1: 200, 2: 300}
        all_in_seats = [0, 1]
        existing_pots = []
        
        pots = PotCalculator.create_pots_from_bets(
            bet_contributions, all_in_seats, existing_pots
        )
        
        # メインポット: 100 * 3 = 300 (全員)
        # サイドポット1: 100 * 2 = 200 (Player 1, 2)
        # サイドポット2: 100 * 1 = 100 (Player 2)
        assert len(pots) == 3
        assert pots[0].amount == 300
        assert set(pots[0].eligible_seats) == {0, 1, 2}
        assert pots[1].amount == 200
        assert set(pots[1].eligible_seats) == {1, 2}
        assert pots[2].amount == 100
        assert set(pots[2].eligible_seats) == {2}
    
    def test_calculate_distribution_single_winner(self):
        """1人勝ちの場合、全ポットを獲得"""
        pots = [
            Pot()
        ]
        pots[0].amount = 300
        pots[0].eligible_seats = [0, 1, 2]
        
        hand_scores = {0: 100, 1: 200, 2: 300}  # 0が最強
        in_hand_seats = [0, 1, 2]
        
        distributions = PotCalculator.calculate_distribution(
            pots, hand_scores, in_hand_seats
        )
        
        assert len(distributions) == 1
        assert distributions[0]["seat_index"] == 0
        assert distributions[0]["amount"] == 300
        assert distributions[0]["pot_type"] == "main"
    
    def test_calculate_distribution_split_pot(self):
        """チョップの場合、ポットを分割"""
        pots = [Pot()]
        pots[0].amount = 300
        pots[0].eligible_seats = [0, 1, 2]
        
        hand_scores = {0: 100, 1: 100, 2: 300}  # 0と1が同点
        in_hand_seats = [0, 1, 2]
        
        distributions = PotCalculator.calculate_distribution(
            pots, hand_scores, in_hand_seats
        )
        
        assert len(distributions) == 2
        # 端数は最初の勝者に
        amounts = {dist["seat_index"]: dist["amount"] for dist in distributions}
        assert amounts[0] == 150
        assert amounts[1] == 150
    
    def test_calculate_distribution_split_pot_with_remainder(self):
        """チョップで割り切れない場合、端数を最初の勝者から配分"""
        pots = [Pot()]
        pots[0].amount = 301  # 3で割り切れない
        pots[0].eligible_seats = [0, 1, 2]
        
        hand_scores = {0: 100, 1: 100, 2: 100}  # 全員同点
        in_hand_seats = [0, 1, 2]
        
        distributions = PotCalculator.calculate_distribution(
            pots, hand_scores, in_hand_seats
        )
        
        assert len(distributions) == 3
        amounts = sorted([dist["amount"] for dist in distributions], reverse=True)
        assert amounts == [101, 100, 100]  # 端数1は最初の勝者に
    
    def test_calculate_distribution_side_pot(self):
        """サイドポット分配のテスト"""
        # メインポット: 300 (全員が対象)
        # サイドポット: 200 (Player 1, 2が対象)
        pots = [Pot(), Pot()]
        pots[0].amount = 300
        pots[0].eligible_seats = [0, 1, 2]
        pots[1].amount = 200
        pots[1].eligible_seats = [1, 2]
        
        hand_scores = {0: 100, 1: 200, 2: 300}  # 0が最強
        in_hand_seats = [0, 1, 2]
        
        distributions = PotCalculator.calculate_distribution(
            pots, hand_scores, in_hand_seats
        )
        
        # Player 0: メインポット300のみ獲得
        # サイドポットの勝者はPlayer 1（次点）
        assert len(distributions) == 2
        
        player_0_win = [d for d in distributions if d["seat_index"] == 0][0]
        assert player_0_win["amount"] == 300
        assert player_0_win["pot_type"] == "main"
        
        player_1_win = [d for d in distributions if d["seat_index"] == 1][0]
        assert player_1_win["amount"] == 200
        assert player_1_win["pot_type"] == "side_1"
    
    def test_calculate_distribution_folded_player_excluded(self):
        """フォールドしたプレイヤーは分配対象外"""
        pots = [Pot()]
        pots[0].amount = 300
        pots[0].eligible_seats = [0, 1, 2]
        
        hand_scores = {0: 100, 1: 200}  # Player 2はフォールド
        in_hand_seats = [0, 1]  # Player 2は除外
        
        distributions = PotCalculator.calculate_distribution(
            pots, hand_scores, in_hand_seats
        )
        
        assert len(distributions) == 1
        assert distributions[0]["seat_index"] == 0
        assert distributions[0]["amount"] == 300
    
    def test_validate_pot_structure_valid(self):
        """正常なポット構造の検証"""
        pots = [Pot(), Pot()]
        pots[0].amount = 300
        pots[0].eligible_seats = [0, 1, 2]
        pots[1].amount = 200
        pots[1].eligible_seats = [1, 2]
        
        is_valid, error = PotCalculator.validate_pot_structure(pots)
        assert is_valid
        assert error == ""
    
    def test_validate_pot_structure_negative_amount(self):
        """負の金額を持つポットは無効"""
        pots = [Pot()]
        pots[0].amount = -100
        pots[0].eligible_seats = [0, 1]
        
        is_valid, error = PotCalculator.validate_pot_structure(pots)
        assert not is_valid
        assert "negative amount" in error
    
    def test_validate_pot_structure_no_eligible_seats(self):
        """金額があるのに対象者がいないポットは無効"""
        pots = [Pot()]
        pots[0].amount = 100
        pots[0].eligible_seats = []
        
        is_valid, error = PotCalculator.validate_pot_structure(pots)
        assert not is_valid
        assert "no eligible seats" in error


class TestPotDistributor:
    """PotDistributor クラスのテスト"""
    
    def test_apply_distribution(self):
        """分配がスタックに正しく反映される"""
        # 座席を準備
        seats = [
            Seat(index=0, player=Player(id="p1", name="Player1")),
            Seat(index=1, player=Player(id="p2", name="Player2")),
            Seat(index=2, player=Player(id="p3", name="Player3"))
        ]
        
        for seat in seats:
            seat.sit_down(seat.player, 1000)
        
        # 分配情報
        distributions = [
            {"seat_index": 0, "amount": 300, "pot_type": "main", "pot_index": 0}
        ]
        
        # 分配前のスタック
        initial_stack = seats[0].stack
        
        # 分配実行
        results = PotDistributor.apply_distribution(seats, distributions)
        
        # 検証
        assert len(results) == 1
        assert results[0]["player_id"] == "p1"
        assert results[0]["seat_index"] == 0
        assert results[0]["pot_won"] == 300
        assert results[0]["pot_type"] == "main"
        
        # スタックが増加していることを確認
        assert seats[0].stack == initial_stack + 300
    
    def test_apply_distribution_multiple_winners(self):
        """複数勝者への分配が正しく実行される"""
        seats = [
            Seat(index=0, player=Player(id="p1", name="Player1")),
            Seat(index=1, player=Player(id="p2", name="Player2")),
        ]
        
        for seat in seats:
            seat.sit_down(seat.player, 1000)
        
        distributions = [
            {"seat_index": 0, "amount": 150, "pot_type": "main", "pot_index": 0},
            {"seat_index": 1, "amount": 150, "pot_type": "main", "pot_index": 0}
        ]
        
        initial_stacks = [seat.stack for seat in seats]
        
        results = PotDistributor.apply_distribution(seats, distributions)
        
        assert len(results) == 2
        assert seats[0].stack == initial_stacks[0] + 150
        assert seats[1].stack == initial_stacks[1] + 150


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
