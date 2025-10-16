# app/game/domain/seat.py
from typing import Optional, List
from .player import Player
from .deck import Card
from .enum import SeatStatus, Position, ActionType

class Seat:
    def __init__(self, index: int, player: Optional[Player]):
        self.index: int = index
        self.player: Optional[Player] = player
        self.starting_stack: int = 0
        self.current_stack: int = 0

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
        return self.is_occupied and self.status == SeatStatus.ACTIVE and self.current_stack > 0
    
    @property
    def in_hand(self) -> bool:
        """この座席が現在のハンドに参加しているかどうか"""
        return self.is_occupied and self.status in {SeatStatus.ACTIVE, SeatStatus.ALL_IN}
    
    def reset_for_new_hand(self) -> None:
        """新しいハンドのために座席の状態をリセットする"""
        self.hole_cards = []
        self.bet_in_hand = 0
        self.reset_for_new_round() # ラウンドごとのリセットも呼び出す
        if self.is_occupied:
            self.status = SeatStatus.ACTIVE if self.current_stack > 0 else SeatStatus.SITTING_OUT

    def reset_for_new_round(self) -> None:
        """新しいベッティングラウンドのために座席の状態をリセットする"""
        self.bet_in_round = 0
        if self.is_active:
            self.last_action = None
            self.acted = False

    def sit_down(self, player: Player, stack: int) -> None:
        """プレイヤーを座席に座らせる"""
        if self.is_occupied:
            raise ValueError(f"Seat {self.index} is already occupied")
        self.player = player
        self.starting_stack = stack
        self.current_stack = stack
        self.status = SeatStatus.ACTIVE

    def stand_up(self) -> None:
        """プレイヤーを座席から外す"""
        self.player = None
        self.status = SeatStatus.EMPTY
        self.current_stack = 0
        self.starting_stack = 0
        self.hole_cards = []
        self.bet_in_round = 0
        self.bet_in_hand = 0

    def pay(self, amount: int) -> None:
        """
        座席にいるプレイヤーが指定額を支払う。
        statusがALL_INになる場合もある。
        """
        if not self.is_occupied:
            raise ValueError(f"Seat {self.index} is empty")
        if amount <= 0:
            raise ValueError("Invalid payment amount")

        pay_amount = min(amount, self.current_stack)

        self.current_stack -= pay_amount
        self.bet_in_round += pay_amount
        self.bet_in_hand += pay_amount
        
        if self.current_stack == 0:
            self.status = SeatStatus.ALL_IN
            self.last_action = ActionType.ALL_IN
   
    def receive_cards(self, cards: List[Card]) -> None:
        """座席にいるプレイヤーがカードを受け取る"""
        if not self.is_occupied:
            raise ValueError(f"Seat {self.index} is empty")
        if len(cards) != 2:
            raise ValueError("A player must receive exactly two hole cards")
        self.hole_cards = cards