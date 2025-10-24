from typing import List, Dict, Tuple
from ..domain.game_state import GameState
from ..domain.table import Pot
from ..domain.seat import Seat
from ..domain.enum import SeatStatus

class PotManager:
    """ポットとサイドポットの計算・管理ロジック"""

    @staticmethod
    def collect_bets_to_pots(game: GameState) -> None:
        """
        各座席のbet_in_roundをポットに回収し、必要に応じてサイドポットを作成する
        
        処理フロー:
        1. 現在のラウンドでベットしているプレイヤーを収集
        2. オールインがない場合: メインポットに全額追加
        3. オールインがある場合: サイドポットを計算して分配
        4. 各座席のbet_in_roundをリセット
        
        重要: FOLDEDプレイヤーのベット額もポットに含めるが、eligible_seatsには含めない
        """
        # 全てのベット額を収集（FOLDEDも含む）
        all_bet_contributions = {
            seat.index: seat.bet_in_round
            for seat in game.table.seats
            if seat.is_occupied and seat.bet_in_round > 0
        }

        if not all_bet_contributions:
            return

        # ポット資格のあるプレイヤー（ACTIVE または ALL_IN）
        eligible_bet_contributions = {
            seat.index: seat.bet_in_round
            for seat in game.table.seats
            if seat.in_hand and seat.bet_in_round > 0
        }

        # このラウンドでオールインしたプレイヤーを取得
        all_in_seats = [
            seat.index for seat in game.table.seats 
            if seat.status == SeatStatus.ALL_IN and seat.bet_in_round > 0
        ]

        # オールインがない場合はシンプルにメインポットに追加
        if not all_in_seats:
            PotManager._add_to_main_pot(game, all_bet_contributions, eligible_bet_contributions)
        else:
            # オールインがある場合はサイドポット計算
            PotManager._create_side_pots(game, all_bet_contributions, eligible_bet_contributions, all_in_seats)

        # 全座席のbet_in_roundをクリア
        for seat in game.table.seats:
            seat.bet_in_round = 0

    @staticmethod
    def _add_to_main_pot(
        game: GameState, 
        all_bet_contributions: Dict[int, int],
        eligible_bet_contributions: Dict[int, int]
    ) -> None:
        """
        全プレイヤーのベットをメインポットに追加
        
        Args:
            game: ゲーム状態
            all_bet_contributions: {座席インデックス: ベット額} (FOLDEDを含む全て)
            eligible_bet_contributions: {座席インデックス: ベット額} (資格のあるプレイヤーのみ)
        """
        # ポット額はFOLDEDも含む全額
        total_bets = sum(all_bet_contributions.values())
        
        # メインポットが存在しない場合は作成
        if not game.table.pots:
            game.table.pots.append(Pot())
        
        # メインポットに追加し、資格者はin_handのプレイヤーのみ
        game.table.main_pot.amount += total_bets
        game.table.main_pot.eligible_seats = list(eligible_bet_contributions.keys())

    @staticmethod
    def _create_side_pots(
        game: GameState, 
        all_bet_contributions: Dict[int, int],
        eligible_bet_contributions: Dict[int, int],
        all_in_seats: List[int]
    ) -> None:
        """
        サイドポット作成ロジック
        
        アルゴリズム:
        1. 資格のあるプレイヤーのベット額を昇順にソート
        2. 各ベットレベルごとにポットを作成（ポット額は全プレイヤーのベットを含む）
        3. オールインプレイヤーは次のポットから除外
        
        例: A=100(FOLDED), B=100, C=200, D=300(ALL_IN)
        - Pot 1: (100+100+200+300) - 余剰分 = 全員の100まで
          eligible: [B, C, D]  ※Aは除外
        - Pot 2: 残りの額から
          eligible: [C, D]  ※Dがオールインなので除外される
        
        Args:
            game: ゲーム状態
            all_bet_contributions: 全プレイヤーのベット額（FOLDEDを含む）
            eligible_bet_contributions: 資格のあるプレイヤーのベット額
            all_in_seats: オールインした座席のインデックスリスト
        """
        # 資格のあるプレイヤーのベット額を昇順にソート
        sorted_bets = sorted(eligible_bet_contributions.items(), key=lambda x: x[1])
        
        current_level = 0  # 現在処理しているベットレベル
        eligible_remaining = list(eligible_bet_contributions.keys())  # まだポットに参加できる資格のあるプレイヤー
        
        # 各プレイヤーの残りベット額を追跡
        remaining_bets = all_bet_contributions.copy()

        for seat_index, bet_amount in sorted_bets:
            # 新しいベットレベルがある場合、ポットを作成
            if bet_amount > current_level:
                contribution_per_player = bet_amount - current_level
                
                # ポット額は、全てのプレイヤー（FOLDEDを含む）の貢献額の合計
                pot_amount = sum(
                    min(remaining_bets.get(idx, 0), contribution_per_player)
                    for idx in remaining_bets.keys()
                )
                
                # 各プレイヤーの残額を更新
                for idx in list(remaining_bets.keys()):
                    contribution = min(remaining_bets[idx], contribution_per_player)
                    remaining_bets[idx] -= contribution
                    if remaining_bets[idx] == 0:
                        del remaining_bets[idx]
                
                # 新しいポットを作成
                new_pot = Pot()
                new_pot.amount = pot_amount
                new_pot.eligible_seats = eligible_remaining.copy()  # 資格者のみ
                game.table.pots.append(new_pot)
                
                current_level = bet_amount
            
            # オールインしたプレイヤーは次のポットから除外
            if seat_index in all_in_seats and seat_index in eligible_remaining:
                eligible_remaining.remove(seat_index)

    @staticmethod
    def calculate_pot_distribution(game: GameState) -> List[dict]:
        """
        ポット分配の計算（実際の分配は行わない）
        
        各ポットについて:
        1. 資格のあるプレイヤーを確認
        2. 最高ハンドを持つプレイヤーを特定
        3. 同点の場合は均等分配（余りは最初の勝者から順に配分）
        
        Args:
            game: ゲーム状態
            
        Returns:
            [{"seat_index": int, "amount": int, "pot_type": str}]
            
        Example:
            [
                {"seat_index": 0, "amount": 150, "pot_type": "main"},
                {"seat_index": 1, "amount": 50, "pot_type": "side_1"}
            ]
        """
        distributions = []
        
        for pot_index, pot in enumerate(game.table.pots):
            if pot.amount == 0:
                continue
            
            # このポットの分配を計算
            pot_distribution = PotManager._distribute_single_pot(
                game, pot, pot_index
            )
            distributions.extend(pot_distribution)
        
        return distributions

    @staticmethod
    def _distribute_single_pot(
        game: GameState, 
        pot: Pot, 
        pot_index: int
    ) -> List[dict]:
        """
        単一のポットの分配を計算
        
        Args:
            game: ゲーム状態
            pot: 分配するポット
            pot_index: ポットのインデックス(0=main, 1以降=side)
            
        Returns:
            このポットの分配結果のリスト
        """
        # このポットの資格者で、まだハンドに残っているプレイヤー
        eligible_in_hand = [
            seat_index for seat_index in pot.eligible_seats
            if game.table.seats[seat_index].in_hand
        ]
        
        if not eligible_in_hand:
            # 誰も資格がない場合（全員フォールド等）
            return []
        
        # 勝者を特定
        winners = PotManager._find_pot_winners(game, eligible_in_hand)
        
        if not winners:
            return []
        
        # ポット額を勝者間で分配
        return PotManager._split_pot_among_winners(pot, winners, pot_index)

    @staticmethod
    def _find_pot_winners(
        game: GameState, 
        eligible_seats: List[int]
    ) -> List[int]:
        """
        資格のあるプレイヤーの中から勝者を見つける
        
        Args:
            game: ゲーム状態
            eligible_seats: このポットの資格がある座席インデックス
            
        Returns:
            勝者の座席インデックスリスト（同点の場合は複数）
        """
        # 最高ハンドを見つける（hand_scoreが最小=最強）
        best_score = min(
            game.table.seats[seat_index].hand_score 
            for seat_index in eligible_seats
        )
        
        # 最高ハンドを持つ全てのプレイヤー
        winners = [
            seat_index for seat_index in eligible_seats
            if game.table.seats[seat_index].hand_score == best_score
        ]
        
        return winners

    @staticmethod
    def _split_pot_among_winners(
        pot: Pot, 
        winners: List[int], 
        pot_index: int
    ) -> List[dict]:
        """
        ポット額を勝者間で分配
        
        Args:
            pot: 分配するポット
            winners: 勝者の座席インデックスリスト
            pot_index: ポットのインデックス
            
        Returns:
            分配結果のリスト
        """
        share_per_winner = pot.amount // len(winners)
        remainder = pot.amount % len(winners)
        
        distributions = []
        for idx, winner_index in enumerate(winners):
            # 余りは最初の勝者から順に1チップずつ配分
            share = share_per_winner + (1 if idx < remainder else 0)
            
            pot_type = "main" if pot_index == 0 else f"side_{pot_index}"
            
            distributions.append({
                "seat_index": winner_index,
                "amount": share,
                "pot_type": pot_type
            })
        
        return distributions