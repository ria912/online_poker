from pydantic import BaseModel, Field
from typing import Optional, Any, Literal

# WebSocket message types used by client/server

class BaseWSMessage(BaseModel):
    type: str = Field(..., description="Message type identifier")


class StartGameMessage(BaseWSMessage):
    type: Literal["start_game"] = "start_game"


class GetStateMessage(BaseWSMessage):
    type: Literal["get_state"] = "get_state"


class ChatMessage(BaseWSMessage):
    type: Literal["chat"] = "chat"
    message: str = Field(..., min_length=0)


class PlayerActionMessage(BaseWSMessage):
    type: Literal["player_action"] = "player_action"
    action: Literal["FOLD", "CHECK", "CALL", "BET", "RAISE", "ALL_IN"]
    amount: int = Field(0, ge=0)


class ErrorMessage(BaseWSMessage):
    type: Literal["error"] = "error"
    error: str


class ServerMessage(BaseModel):
    type: str
    data: Optional[Any] = None
    error: Optional[str] = None
