# app/game/domain/enum.py
from enum import Enum

class Position(str, Enum):
    SB = "SB"
    BB = "BB"
    LJ = "LJ"
    HJ = "HJ"
    CO = "CO"
    BTN = "BTN"


class Round(str, Enum):
    PREFLOP = "PREFLOP"
    FLOP = "FLOP"
    TURN = "TURN"
    RIVER = "RIVER"
    SHOWDOWN = "SHOWDOWN"


class SeatStatus(str, Enum):
    EMPTY = "EMPTY"     # プレイヤーが座っていない
    ACTIVE = "ACTIVE"
    FOLDED = "FOLDED"
    ALL_IN = "ALL_IN"
    SITTING_OUT = "SITTING_OUT"


class GameStatus(str, Enum):
    WAITING = "WAITING"             # プレイヤー待ち
    IN_PROGRESS = "IN_PROGRESS"     # ゲーム中
    ROUND_OVER = "ROUND_OVER"       # ラウンド終了、次のラウンドへ進む準備完了
    BETTING_OVER = "BETTING_OVER"   # in_handのプレイヤーをショウダウンに進める
    HAND_COMPLETE = "HAND_COMPLETE" # ゲーム終了、勝者決定


class ActionType(str, Enum):
    FOLD = "FOLD"
    CHECK = "CHECK"
    CALL = "CALL"
    BET = "BET"
    RAISE = "RAISE"
    ALL_IN = "ALL_IN"