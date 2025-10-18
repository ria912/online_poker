# app/game/domain/seat.py
from typing import Optional, List
from .player import Player
from .deck import Card
from .enum import SeatStatus, Position, ActionType

class Seat:
    def __init__(self, index: int, player: Optional[Player]):
        self.index: int = index
        self.player: Optional[Player] = player
        self.stack: int = 0
        self.hole_cards: List[Card] = []
        self.position: Optional[Position] = None
        self.bet_in_round: int = 0
        self.bet_in_hand: int = 0

        self.last_action: Optional[ActionType] = None
        self.status: SeatStatus = SeatStatus.EMPTY
        self.acted: bool = False
        self.hand_score: int = 9999
        self.show_hand: bool = False

    @property
    def is_occupied(self) -> bool:
        """プレイヤーが座っているかどうか"""
        return self.player is not None
    
    @property
    def is_active(self) -> bool:
        """この座席がアクティブかどうか"""
        return self.is_occupied and self.status == SeatStatus.ACTIVE and self.stack > 0
    
    @property
    def in_hand(self) -> bool:
        """この座席が現在のハンドに参加しているかどうか"""
        return self.is_occupied and self.status in {SeatStatus.ACTIVE, SeatStatus.ALL_IN}
    
    def pay(self, amount: int) -> int:
        """支払いを実行し、実際の支払額を返す（整合性を一元管理）"""
        actual = min(amount, self.stack)
        self.stack -= actual
        self.bet_in_round += actual
        self.bet_in_hand += actual
        return actual
    
    def refund(self, amount: int) -> None:
        """払い戻し"""
        self.stack += amount
    
    def clear_for_new_hand(self) -> None:
        """新しいハンドのために座席の状態をリセットする"""
        self.hole_cards.clear()
        self.bet_in_round = 0
        self.bet_in_hand = 0
        if self.is_occupied:
            self.status = SeatStatus.ACTIVE if self.stack > 0 else SeatStatus.SITTING_OUT

    def reset_for_new_round(self) -> None:
        """新しいベッティングラウンドのために座席の状態をリセットする"""
        self.bet_in_round = 0
        if self.is_active:
            self.last_action = None
            self.acted = False

    def sit_down(self, player: Player, stack: int = 0) -> None:
        """プレイヤーを座席に座らせる"""
        if self.is_occupied:
            raise ValueError(f"Seat {self.index} is already occupied")
        self.player = player
        self.stack = stack
        self.status = SeatStatus.ACTIVE

    def stand_up(self) -> None:
        """プレイヤーを座席から外す"""
        self.player = None
        self.stack = 0
        self.status = SeatStatus.EMPTY
        self.hole_cards = []
        self.bet_in_round = 0
        self.bet_in_hand = 0
   
    def receive_cards(self, cards: List[Card]) -> None:
        """座席にいるプレイヤーがカードを受け取る"""
        if not self.is_occupied:
            raise ValueError(f"Seat {self.index} is empty")
        if len(cards) != 2:
            raise ValueError("A player must receive exactly two hole cards")
        self.hole_cards = cards