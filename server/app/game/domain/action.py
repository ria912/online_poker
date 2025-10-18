# app/game/domain/action.py
from typing import Optional
from dataclasses import dataclass
from .enum import ActionType


@dataclass(frozen=True)
class PlayerAction:
    """プレイヤーのアクションを表すクラス"""
    player_id: str
    action_type: ActionType
    amount: int = 0