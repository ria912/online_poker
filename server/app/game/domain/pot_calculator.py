# app/game/domain/pot_calculator.py
from typing import List, Dict, Tuple
from .table import Pot


class PotCalculator:
    """
    ポット計算のビジネスロジック
    
    責務:
    - ベット額からポット構造を計算
    - サイドポット生成ロジック
    - ポット分配計算（勝者決定は除く）
    
    ドメイン知識:
    - オールイン時のサイドポット生成ルール
    - 複数勝者時の端数処理ルール
    """
    
    @staticmethod
    def create_pots_from_bets(
        bet_contributions: Dict[int, int],
        all_in_seats: List[int],
        existing_pots: List[Pot]
    ) -> List[Pot]:
        """
        ベット額からポット構造を生成
        
        Args:
            bet_contributions: {seat_index: bet_amount} - 各座席の今回のベット額
            all_in_seats: オールインした座席のインデックスリスト
            existing_pots: 既存のポットリスト（継続して使用）
        
        Returns:
            更新されたポットリスト
        """
        if not bet_contributions:
            return existing_pots
        
        # オールインがない場合：メインポットに全額追加
        if not all_in_seats:
            return PotCalculator._add_to_main_pot(bet_contributions, existing_pots)
        
        # オールインがある場合：サイドポット計算
        return PotCalculator._create_side_pots(bet_contributions, all_in_seats, existing_pots)
    
    @staticmethod
    def _add_to_main_pot(
        bet_contributions: Dict[int, int],
        existing_pots: List[Pot]
    ) -> List[Pot]:
        """メインポットに全額を追加"""
        total_bets = sum(bet_contributions.values())
        
        # メインポットがなければ作成
        if not existing_pots:
            main_pot = Pot()
            main_pot.amount = total_bets
            main_pot.eligible_seats = list(bet_contributions.keys())
            existing_pots.append(main_pot)
        else:
            # 既存のメインポットに追加
            existing_pots[0].amount += total_bets
            # 対象者を更新（新しい参加者を追加）
            for seat_index in bet_contributions.keys():
                if seat_index not in existing_pots[0].eligible_seats:
                    existing_pots[0].eligible_seats.append(seat_index)
        
        return existing_pots
    
    @staticmethod
    def _create_side_pots(
        bet_contributions: Dict[int, int],
        all_in_seats: List[int],
        existing_pots: List[Pot]
    ) -> List[Pot]:
        """
        オールイン発生時にサイドポットを作成
        
        アルゴリズム:
        1. ベット額でソート（昇順）
        2. 各レベルでポットを作成
        3. オールインプレイヤーは次のポットから除外
        """
        # ベット額でソート（昇順）
        sorted_bets = sorted(bet_contributions.items(), key=lambda x: x[1])
        
        current_level = 0
        remaining_players = list(bet_contributions.keys())
        pots = existing_pots.copy() if existing_pots else []
        
        for seat_index, bet_amount in sorted_bets:
            if bet_amount > current_level:
                contribution = bet_amount - current_level
                pot_amount = contribution * len(remaining_players)
                
                # 新しいポット作成
                new_pot = Pot()
                new_pot.amount = pot_amount
                new_pot.eligible_seats = remaining_players.copy()
                pots.append(new_pot)
                
                current_level = bet_amount
            
            # オールインプレイヤーは次のポットから除外
            if seat_index in all_in_seats and seat_index in remaining_players:
                remaining_players.remove(seat_index)
        
        return pots
    
    @staticmethod
    def calculate_distribution(
        pots: List[Pot],
        hand_scores: Dict[int, int],
        in_hand_seats: List[int]
    ) -> List[Dict]:
        """
        ポット分配を計算（勝者スコアに基づく）
        
        Args:
            pots: 分配対象のポットリスト
            hand_scores: {seat_index: hand_score} - 各座席のハンドスコア（小さいほど強い）
            in_hand_seats: ハンドに残っている座席インデックスリスト
        
        Returns:
            [{"seat_index": int, "amount": int, "pot_type": str, "pot_index": int}]
        """
        distributions = []
        
        for pot_index, pot in enumerate(pots):
            if pot.amount == 0:
                continue
            
            # このポットの対象者で現在もin_handの座席
            eligible_in_hand = [
                seat_index for seat_index in pot.eligible_seats
                if seat_index in in_hand_seats
            ]
            
            if not eligible_in_hand:
                continue
            
            # 最高ハンドを見つける（hand_scoreが最小）
            eligible_scores = {
                seat_index: hand_scores[seat_index] 
                for seat_index in eligible_in_hand
                if seat_index in hand_scores
            }
            
            if not eligible_scores:
                continue
            
            best_score = min(eligible_scores.values())
            
            # 勝者リスト
            winners = [
                seat_index for seat_index, score in eligible_scores.items()
                if score == best_score
            ]
            
            # ポットを分配（端数処理）
            share_per_winner = pot.amount // len(winners)
            remainder = pot.amount % len(winners)
            
            for j, winner_index in enumerate(winners):
                # 端数は最初の勝者から順に1チップずつ配分
                share = share_per_winner + (1 if j < remainder else 0)
                distributions.append({
                    "seat_index": winner_index,
                    "amount": share,
                    "pot_type": "main" if pot_index == 0 else f"side_{pot_index}",
                    "pot_index": pot_index
                })
        
        return distributions
    
    @staticmethod
    def validate_pot_structure(pots: List[Pot]) -> Tuple[bool, str]:
        """
        ポット構造の整合性を検証
        
        Returns:
            (is_valid, error_message)
        """
        if not pots:
            return True, ""
        
        # 各ポットの金額が正の数か
        for i, pot in enumerate(pots):
            if pot.amount < 0:
                return False, f"Pot {i} has negative amount: {pot.amount}"
        
        # 各ポットに対象者がいるか
        for i, pot in enumerate(pots):
            if pot.amount > 0 and not pot.eligible_seats:
                return False, f"Pot {i} has amount but no eligible seats"
        
        # サイドポットの対象者はメインポットのサブセットか
        if len(pots) > 1:
            main_eligible = set(pots[0].eligible_seats)
            for i, pot in enumerate(pots[1:], start=1):
                side_eligible = set(pot.eligible_seats)
                if not side_eligible.issubset(main_eligible):
                    return False, f"Side pot {i} eligible seats are not subset of main pot"
        
        return True, ""


class PotDistributor:
    """
    ポット分配の実行を担当
    
    責務:
    - 計算済みの分配情報を実際のスタックに反映
    - 分配履歴の記録
    """
    
    @staticmethod
    def apply_distribution(
        seats: List,  # List[Seat] - 循環参照回避のため型ヒントなし
        distributions: List[Dict]
    ) -> List[Dict]:
        """
        分配をスタックに反映
        
        Args:
            seats: 座席リスト
            distributions: PotCalculator.calculate_distribution() の返り値
        
        Returns:
            実際に払い戻された情報のリスト
            [{"player_id": str, "seat_index": int, "amount": int, "pot_type": str}]
        """
        results = []
        
        for dist in distributions:
            seat_index = dist["seat_index"]
            amount = dist["amount"]
            
            # スタックに払い戻し
            seat = seats[seat_index]
            seat.refund(amount)
            
            results.append({
                "player_id": seat.player.id if seat.player else None,
                "seat_index": seat_index,
                "hand_score": getattr(seat, "hand_score", None),
                "pot_won": amount,
                "pot_type": dist["pot_type"]
            })
        
        return results
