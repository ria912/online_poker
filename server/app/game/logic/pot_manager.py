from typing import List, Dict
from ..domain.game_state import GameState
from ..domain.table import Pot
from ..domain.enum import SeatStatus

class PotManager:
    """ポットとサイドポットの計算・管理ロジック"""

    @staticmethod
    def collect_bets_to_pots(game: GameState) -> None:
        """
        各座席のbet_in_roundをポットに回収し、サイドポットを作成
        """
        bet_contributions = {}
        for seat in game.table.seats:
            if seat.in_hand and seat.bet_in_round > 0:
                bet_contributions[seat.index] = seat.bet_in_round

        if not bet_contributions:
            return

        all_in_seats = [seat.index for seat in game.table.seats if seat.status == SeatStatus.ALL_IN]

        if not all_in_seats:
            total_bets = sum(bet_contributions.values())
            if not game.table.pots:
                main_pot = Pot()
                main_pot.amount = 0
                main_pot.eligible_seats = list(bet_contributions.keys())
                game.table.pots.append(main_pot)
            game.table.pots[0].amount += total_bets
        else:
            PotManager._create_side_pots(game, bet_contributions, all_in_seats)

        for seat in game.table.seats:
            seat.bet_in_round = 0

    @staticmethod
    def _create_side_pots(game: GameState, bet_contributions: Dict[int, int], all_in_seats: List[int]) -> None:
        """
        サイドポット作成ロジック
        """
        sorted_bets = sorted(bet_contributions.items(), key=lambda x: x[1])
        current_level = 0
        remaining_players = list(bet_contributions.keys())

        for seat_index, bet_amount in sorted_bets:
            if bet_amount > current_level:
                contribution = bet_amount - current_level
                pot_amount = contribution * len(remaining_players)
                if not game.table.pots:
                    main_pot = Pot()
                    main_pot.amount = pot_amount
                    main_pot.eligible_seats = remaining_players.copy()
                    game.table.pots.append(main_pot)
                else:
                    side_pot = Pot()
                    side_pot.amount = pot_amount
                    side_pot.eligible_seats = remaining_players.copy()
                    game.table.pots.append(side_pot)
                current_level = bet_amount
            if seat_index in all_in_seats and seat_index in remaining_players:
                remaining_players.remove(seat_index)

    @staticmethod
    def calculate_pot_distribution(game: GameState) -> List[dict]:
        """
        ポット分配の計算（実際の分配は行わない）
        
        Args:
            game: ゲーム状態
            
        Returns:
            [{"seat_index": int, "amount": int, "pot_type": str}]
        """
        distributions = []
        
        for i, pot in enumerate(game.table.pots):
            if pot.amount == 0:
                continue
            
            # このポットの対象者で現在もin_handの座席
            eligible_in_hand = [
                seat_index for seat_index in pot.eligible_seats
                if game.table.seats[seat_index].in_hand
            ]
            
            if not eligible_in_hand:
                continue
            
            # 最高ハンドを見つける（hand_scoreが最小）
            best_score = min(
                game.table.seats[seat_index].hand_score 
                for seat_index in eligible_in_hand
            )
            
            winners = [
                seat_index for seat_index in eligible_in_hand
                if game.table.seats[seat_index].hand_score == best_score
            ]
            
            # ポットを分配
            share_per_winner = pot.amount // len(winners)
            remainder = pot.amount % len(winners)
            
            for j, winner_index in enumerate(winners):
                share = share_per_winner + (1 if j < remainder else 0)
                distributions.append({
                    "seat_index": winner_index,
                    "amount": share,
                    "pot_type": "main" if i == 0 else f"side_{i}"
                })
        
        return distributions