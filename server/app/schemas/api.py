from pydantic import BaseModel, Field
from typing import List

class CreateSinglePlayRequest(BaseModel):
    big_blind: int = Field(default=100, ge=10, le=1000)
    buy_in: int = Field(default=10000, ge=1000, le=100000)


class CreateSinglePlayResponse(BaseModel):
    game_id: str
    message: str
    ai_players: List[str]
    websocket_url: str


class GameStateResponse(BaseModel):
    game_id: str
    status: str
    player_count: int
    seated_count: int
