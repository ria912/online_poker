# server/app/game/services/game_service.py
from typing import Dict, Optional, List
import asyncio
from ..domain.game_state import GameState
from ..domain.player import Player
from ..domain.action import PlayerAction
from ..domain.enum import ActionType, GameStatus
from .poker_engine import PokerEngine


class GameService:
    """ゲーム管理の中心的なサービス"""
    
    def __init__(self):
        self.games: Dict[str, GameState] = {}
        self.poker_engine = PokerEngine()
    
    async def create_game(self, game_id: str, big_blind: int = 100) -> GameState:
        """新しいゲームを作成"""
        if game_id in self.games:
            raise ValueError(f"Game {game_id} already exists")
        
        game = GameState(big_blind=big_blind, small_blind=big_blind//2)
        self.games[game_id] = game
        return game
    
    async def join_game(self, game_id: str, player: Player) -> bool:
        """プレイヤーをゲームに参加させる"""
        game = self.games.get(game_id)
        if not game:
            return False
        
        # 空席に自動配置
        success = await self.poker_engine.seat_player(game, player)
        return success
    
    async def start_game(self, game_id: str) -> bool:
        """ゲームを開始"""
        game = self.games.get(game_id)
        if not game:
            return False
        
        # 最低2人のプレイヤーが必要
        active_players = [seat for seat in game.table.seats if seat.is_active]
        if len(active_players) < 2:
            return False
        
        return await self.poker_engine.start_new_hand(game)
    
    async def process_player_action(
        self, 
        game_id: str, 
        player_id: str, 
        action_type: ActionType, 
        amount: Optional[int] = None
    ) -> bool:
        """プレイヤーアクションを処理"""
        game = self.games.get(game_id)
        if not game:
            return False
        
        action = PlayerAction(player_id=player_id, action_type=action_type, amount=amount or 0)
        return await self.poker_engine.process_action(game, action)
    
    def get_game_state(self, game_id: str) -> Optional[GameState]:
        """ゲーム状態を取得"""
        return self.games.get(game_id)
    
    def get_valid_actions(self, game_id: str, player_id: str) -> List[ActionType]:
        """プレイヤーの有効なアクションを取得"""
        game = self.games.get(game_id)
        if not game:
            return []
        
        return self.poker_engine.get_valid_actions(game, player_id)


# グローバルサービスインスタンス
game_service = GameService()