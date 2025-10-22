# app/game/services/dealer_service.py
from typing import List, Optional, Dict
from ..domain.game_state import GameState
from ..domain.table import Pot
from ..domain.enum import SeatStatus, Round
from ..domain.deck import Card
from ..domain.pot_calculator import PotCalculator, PotDistributor


class DealerService:
    """ディーラーの責務を担当するサービス"""
    
    def __init__(self):
        pass
    
    def distribute_pots(self, game: GameState) -> List[dict]:
        """
        ポット分配を計算し、勝者のスタックにチップを移動する
        
        Returns:
            [{"player_id": str, "seat_index": int, "hand_score": int, "pot_won": int, "pot_type": str}]
        """
        # ハンドスコアを収集
        hand_scores = {
            seat.index: seat.hand_score 
            for seat in game.table.seats 
            if seat.in_hand and hasattr(seat, 'hand_score')
        }
        
        # ハンドに残っている座席
        in_hand_seats = [seat.index for seat in game.table.seats if seat.in_hand]
        
        # ポット分配を計算（ドメインロジック）
        distributions = PotCalculator.calculate_distribution(
            pots=game.table.pots,
            hand_scores=hand_scores,
            in_hand_seats=in_hand_seats
        )
        
        # スタックに反映（実行）
        results = PotDistributor.apply_distribution(
            seats=game.table.seats,
            distributions=distributions
        )
        
        return results
    
    def collect_bets_to_pots(self, game: GameState) -> None:
        """
        ラウンド終了時に各座席のbet_in_roundをポットに回収する
        オールイン発生時にサイドポットを作成
        """
        # 現在のベット状況を取得
        bet_contributions = {}
        for seat in game.table.seats:
            if seat.in_hand and seat.bet_in_round > 0:
                bet_contributions[seat.index] = seat.bet_in_round
        
        if not bet_contributions:
            return
        
        # オールインプレイヤーを検出
        all_in_seats = [seat.index for seat in game.table.seats if seat.status == SeatStatus.ALL_IN]
        
        # ドメインロジックでポット構造を計算
        game.table.pots = PotCalculator.create_pots_from_bets(
            bet_contributions=bet_contributions,
            all_in_seats=all_in_seats,
            existing_pots=game.table.pots
        )
        
        # 各座席のbet_in_roundをクリア
        for seat in game.table.seats:
            seat.bet_in_round = 0
    
    def _create_side_pots(self, game: GameState, bet_contributions: dict, all_in_seats: List[int]) -> None:
        """
        [DEPRECATED] オールイン発生時にサイドポットを作成
        
        このメソッドは PotCalculator.create_pots_from_bets() に置き換えられました。
        後方互換性のため残していますが、使用は推奨されません。
        """
        game.table.pots = PotCalculator.create_pots_from_bets(
            bet_contributions=bet_contributions,
            all_in_seats=all_in_seats,
            existing_pots=game.table.pots
        )
    
    def rotate_dealer_button(self, game: GameState) -> None:
        """
        ディーラーボタンを次のアクティブプレイヤーに移動
        """
        if game.dealer_seat_index is None:
            # 初回設定：最初のアクティブプレイヤー
            for seat in game.table.seats:
                if seat.is_active:
                    game.dealer_seat_index = seat.index
                    break
            return
        # 次のアクティブプレイヤーを探す
        next_dealer_index = self._get_next_active_seat_index(game, game.dealer_seat_index)
        if next_dealer_index is None:
            return  # アクティブプレイヤーが見つからない
        
        game.dealer_seat_index = next_dealer_index
    
    def set_blind_positions(self, game: GameState) -> None:
        """ブラインドポジションを設定"""
        if game.dealer_seat_index is None:
            return
        
        active_seats = [seat for seat in game.table.seats if seat.is_active]
        if len(active_seats) < 2:
            return
        
        # ヘッズアップの場合
        if len(active_seats) == 2:
            # ディーラー（ボタン）がSB、相手がBB
            game.small_blind_seat_index = game.dealer_seat_index
            game.big_blind_seat_index = self._get_next_active_seat_index(game, game.dealer_seat_index)
        else:
            # 3人以上の場合
            game.small_blind_seat_index = self._get_next_active_seat_index(game, game.dealer_seat_index)
            if game.small_blind_seat_index is not None:
                game.big_blind_seat_index = self._get_next_active_seat_index(game, game.small_blind_seat_index)
    
    def collect_blinds(self, game: GameState) -> None:
        """ブラインドを徴収"""
        if game.small_blind_seat_index is not None:
            sb_seat = game.table.seats[game.small_blind_seat_index]
            if sb_seat.is_active:
                sb_seat.pay(game.small_blind)
                sb_seat.status = SeatStatus.ACTIVE if sb_seat.stack > 0 else SeatStatus.ALL_IN
        
        if game.big_blind_seat_index is not None:
            bb_seat = game.table.seats[game.big_blind_seat_index]
            if bb_seat.is_active:
                bb_seat.pay(game.big_blind)
                bb_seat.status = SeatStatus.ACTIVE if bb_seat.stack > 0 else SeatStatus.ALL_IN
                # 現在のベット額を設定
                game.current_bet = max(sb_seat.bet_in_round, bb_seat.bet_in_round)
    
    def deal_hole_cards(self, game: GameState) -> None:
        """各プレイヤーにホールカードを配布"""
        in_hand_seats = game.table.in_hand_seats()
        game.table.deck.shuffle()
        # 各プレイヤーに2枚ずつ配布
        for seat in in_hand_seats:
            hole_cards = game.table.deck.draw(2)
            seat.receive_cards(hole_cards)
    
    def deal_community_cards(self, game: GameState) -> None:
        """コミュニティカードを配布"""
        if game.current_round == Round.PREFLOP:
            self._deal_flop(game)
        elif game.current_round == Round.FLOP:
            self._deal_turn(game)
        elif game.current_round == Round.TURN:
            self._deal_river(game)
    
    def _deal_flop(self, game: GameState) -> None:
        """フロップ（3枚）を配布"""
        if len(game.table.community_cards) > 0:
            return  # 既に配布済み
        game.current_round = Round.FLOP
        flop_cards = game.table.deck.draw(3)
        game.table.community_cards.extend(flop_cards)
    
    def _deal_turn(self, game: GameState) -> None:
        """ターン（4枚目）を配布"""
        if len(game.table.community_cards) != 3:
            return  # フロップが未配布
        game.current_round = Round.TURN
        turn_card = game.table.deck.draw(1)
        game.table.community_cards.extend(turn_card)
    
    def _deal_river(self, game: GameState) -> None:
        """リバー（5枚目）を配布"""
        if len(game.table.community_cards) != 4:
            return  # ターンが未配布
        game.current_round = Round.RIVER
        river_card = game.table.deck.draw(1)
        game.table.community_cards.extend(river_card)
    
    def setup_new_hand(self, game: GameState) -> bool:
        """新しいハンドのセットアップ"""
        active_seats = [seat for seat in game.table.seats if seat.is_active]
        if len(active_seats) < 2:
            return False

        self.rotate_dealer_button(game)
        self.set_blind_positions(game)
        self.collect_blinds(game)
        self.deal_hole_cards(game)
        return True
    
    def _get_next_active_seat_index(self, game: GameState, current_index: int) -> Optional[int]:
        """次のアクティブな座席インデックスを取得"""
        seats_count = len(game.table.seats)
        
        for i in range(1, seats_count):
            next_index = (current_index + i) % seats_count
            seat = game.table.seats[next_index]
            if seat.is_active:
                return next_index
        
        return None
    
    def calculate_pot_distribution(self, game: GameState) -> List[dict]:
        """
        [DEPRECATED] ポット分配の計算（実際の分配は行わない）
        
        このメソッドは PotCalculator.calculate_distribution() に置き換えられました。
        後方互換性のため残していますが、使用は推奨されません。
        
        Returns:
            [{"seat_index": int, "amount": int, "pot_type": str}]
        """
        hand_scores = {
            seat.index: seat.hand_score 
            for seat in game.table.seats 
            if seat.in_hand and hasattr(seat, 'hand_score')
        }
        
        in_hand_seats = [seat.index for seat in game.table.seats if seat.in_hand]
        
        distributions = PotCalculator.calculate_distribution(
            pots=game.table.pots,
            hand_scores=hand_scores,
            in_hand_seats=in_hand_seats
        )
        
        # 旧フォーマットに変換（後方互換性）
        return [
            {
                "seat_index": dist["seat_index"],
                "amount": dist["amount"],
                "pot_type": dist["pot_type"]
            }
            for dist in distributions
        ]
