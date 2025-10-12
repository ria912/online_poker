# app/game/domain/table.py
from typing import List, Optional
from .deck import Deck, Card
from .player import Player
from .seat import Seat
from .enum import SeatStatus

class Pot:
    """
    amount (int): このポットに含まれるチップの合計額。
    eligible_seats (List[int]): このポットを獲得する資格のあるSeatのインデックス。
    """
    def __init__(self):
        self.amount: int = 0
        self.eligible_seats: List[int] = []

class Table:
    def __init__(self, seat_count: int = 6):
        self.deck = Deck()
        self.seats: List[Seat] = [Seat(index=i, player=None) for i in range(seat_count)]
        self.community_cards: List[Card] = []
        self.pots: List[Pot] = [Pot()]
        
    @property
    def total_pot(self) -> int:
        """現在のすべてのポットの合計額を計算する"""
        return sum(pot.amount for pot in self.pots)

    @property
    def is_hand_over(self) -> bool:
        """現在のハンドが終了しているかどうか"""
        return len(self.in_hand_players()) == 1
    
    @property
    def is_betting_over(self) -> bool:
        """以降ベッティングが存在するかどうか"""
        return len(self.active_players()) == 1

    def reset_for_new_hand(self):
        """テーブルの状態を新しいハンドのためにリセットする"""
        self.deck = Deck()
        self.community_cards = []
        self.pots = [Pot()]
        for seat in self.seats:
            seat.reset_for_new_hand()
    
    def reset_for_new_round(self):
        """テーブルの状態を新しいベッティングラウンドのためにリセットする"""
        for seat in self.seats:
            seat.reset_for_new_round()

    def sit_player(self, player: Player, seat_index: int, stack: int= 10000) -> None:
        """指定した座席にプレイヤーを座らせる"""
        if not (0 <= seat_index < len(self.seats)):
            raise IndexError("Invalid seat index")
        self.seats[seat_index].sit_down(player, stack)

    def stand_player(self, seat_index: int) -> None:
        """指定した座席からプレイヤーを立たせる"""
        if not (0 <= seat_index < len(self.seats)):
            raise IndexError("Invalid seat index")
        
        self.seats[seat_index].stand_up()

    def in_hand_players(self) -> List[Player]:
        """現在のハンドに参加しているプレイヤー一覧を返す"""
        return [seat.player for seat in self.seats if seat.in_hand]

    def active_players(self) -> List[Player]:
        """アクティブなプレイヤー一覧を返す"""
        return [seat.player for seat in self.seats if seat.is_active]

    def empty_seats(self) -> List[int]:
        """空席のインデックス一覧を返す"""
        return [seat.index for seat in self.seats if seat.status == SeatStatus.EMPTY]

