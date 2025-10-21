# app/game/services/dealer_service.py
from typing import List, Optional
from ..domain.game_state import GameState
from ..domain.table import Pot
from ..domain.enum import SeatStatus, Round
from ..domain.deck import Card


class DealerService:
    """ディーラーの責務を担当するサービス"""
    
    def __init__(self):
        pass
    
    def collect_bets_to_pots(self, game: GameState) -> None:
        """
        ラウンド終了時に各座席のbet_in_roundをポットに回収する
        サイドポット計算も含む
        """
        # 現在のベット状況を取得
        bet_contributions = {}
        for seat in game.table.seats:
            if seat.in_hand and seat.bet_in_round > 0:
                bet_contributions[seat.index] = seat.bet_in_round
        
        if not bet_contributions:
            return
        
        # 既存のポットをクリア（新しく計算するため）
        game.table.pots = []
        
        # ベット額でソート（昇順）
        sorted_bets = sorted(bet_contributions.items(), key=lambda x: x[1])
        
        current_level = 0
        eligible_players = list(bet_contributions.keys())
        
        for seat_index, bet_amount in sorted_bets:
            if bet_amount > current_level:
                # 新しいポットまたは既存ポットに追加
                pot_amount = (bet_amount - current_level) * len(eligible_players)
                
                if not game.table.pots:
                    # メインポット作成
                    main_pot = Pot()
                    main_pot.amount = pot_amount
                    main_pot.eligible_seats = eligible_players.copy()
                    game.table.pots.append(main_pot)
                else:
                    # サイドポット作成
                    side_pot = Pot()
                    side_pot.amount = pot_amount
                    side_pot.eligible_seats = eligible_players.copy()
                    game.table.pots.append(side_pot)
                
                current_level = bet_amount
            
            # このプレイヤーをオールインとして除外
            if seat_index in eligible_players:
                eligible_players.remove(seat_index)
        
        # 各座席のbet_in_roundをクリア
        for seat in game.table.seats:
            seat.bet_in_round = 0
    
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
        
        if game.big_blind_seat_index is not None:
            bb_seat = game.table.seats[game.big_blind_seat_index]
            if bb_seat.is_active:
                bb_seat.pay(game.big_blind)
                bb_seat.last_action = None if bb_seat.stack > 0 else SeatStatus.ALL_IN
                bb_seat.acted = False
                # 現在のベット額を設定
                game.current_bet = max(sb_seat.bet_in_round, bb_seat.bet_in_round)
    
    def deal_hole_cards(self, game: GameState) -> None:
        """各プレイヤーにホールカードを配布"""
        active_seats = [seat for seat in game.table.seats if seat.in_hand]
        
        # デッキをシャッフル
        game.table.deck.shuffle()
        
        # 各プレイヤーに2枚ずつ配布
        for seat in active_seats:
            hole_cards = game.table.deck.draw(2)
            seat.receive_cards(hole_cards)
    
    def deal_community_cards(self, game: GameState, round_type: Round) -> None:
        """コミュニティカードを配布"""
        if round_type == Round.PREFLOP:
            self._deal_flop(game)
        elif round_type == Round.FLOP:
            self._deal_turn(game)
        elif round_type == Round.TURN:
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
        self.deal_hole_cards(game)
        self.collect_blinds(game)
        
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
        ポット分配の計算（実際の分配は行わない）
        返り値: [{"seat_index": int, "amount": int, "pot_type": str}]
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