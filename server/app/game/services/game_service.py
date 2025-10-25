# server/app/game/services/game_service.py
from typing import Dict, Optional, List
import asyncio
import uuid
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
        success = self.poker_engine.seat_player(game, player)
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
        
        return self.poker_engine.start_new_hand(game)
    
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
    
    async def create_single_play_game(self, big_blind: int = 100, buy_in: int = 10000) -> GameState:
        """
        シングルプレイ用のゲームを作成（AI 2名を自動追加）
        
        Args:
            big_blind: ビッグブラインド額
            buy_in: 各プレイヤーの初期スタック
            
        Returns:
            GameState: 作成されたゲーム状態
        """
        # ユニークなゲームIDを生成
        game_id = str(uuid.uuid4())
        
        # ゲーム作成
        game = await self.create_game(game_id, big_blind)
        
        # AI プレイヤーを2名作成して追加
        ai1 = Player(player_id=str(uuid.uuid4()), name="AI_Player_1", is_ai=True)
        ai2 = Player(player_id=str(uuid.uuid4()), name="AI_Player_2", is_ai=True)
        
        game.add_player(ai1)
        game.add_player(ai2)
        
        # AIを座席に配置（座席1と2）
        self.poker_engine.seat_player(game, ai1, seat_index=1, buy_in=buy_in)
        self.poker_engine.seat_player(game, ai2, seat_index=2, buy_in=buy_in)
        
        return game
    
    async def setup_single_play_seats(
        self, 
        game_id: str, 
        human_player: Player,
        buy_in: int = 10000
    ) -> bool:
        """
        シングルプレイの座席配置（人間プレイヤーを座席0に配置）
        
        Args:
            game_id: ゲームID
            human_player: 人間プレイヤー
            buy_in: 購入チップ額
            
        Returns:
            bool: 成功した場合True
        """
        game = self.games.get(game_id)
        if not game:
            return False
        
        # 人間プレイヤーをゲームに追加
        game.add_player(human_player)
        
        # 座席0に人間プレイヤーを配置
        success = self.poker_engine.seat_player(game, human_player, seat_index=0, buy_in=buy_in)
        
        return success


# グローバルサービスインスタンス
game_service = GameService()