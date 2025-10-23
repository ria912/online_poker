# app/game/domain/player.py
from typing import Optional, List
from .deck import Card

class Player:
    def __init__(self, player_id: str, name: str, is_ai: bool = True):
        self.id: str = player_id
        self.name: str = name
        self.is_ai: bool = is_ai
        self.messages: List[str] = []  # チャットメッセージ履歴
