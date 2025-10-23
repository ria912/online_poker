"""
ゲーム用WebSocket接続マネージャー
"""
from fastapi import WebSocket
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class GameConnectionManager:
    """ゲーム接続を管理するクラス"""
    
    def __init__(self):
        # ゲームID -> {player_id: websocket}
        self.active_games: Dict[str, Dict[str, WebSocket]] = {}
        # websocket -> (game_id, player_id)
        self.connections: Dict[WebSocket, tuple] = {}
    
    async def connect(self, websocket: WebSocket, game_id: str, player_id: str):
        """プレイヤーをゲームに接続"""
        await websocket.accept()
        
        if game_id not in self.active_games:
            self.active_games[game_id] = {}
        
        self.active_games[game_id][player_id] = websocket
        self.connections[websocket] = (game_id, player_id)
        
        logger.info(f"Player {player_id} connected to game {game_id}")
    
    def disconnect(self, websocket: WebSocket) -> Optional[tuple]:
        """プレイヤーの接続を切断"""
        if websocket not in self.connections:
            return None
        
        game_id, player_id = self.connections[websocket]
        
        # 接続情報を削除
        if game_id in self.active_games:
            self.active_games[game_id].pop(player_id, None)
            
            # ゲームに誰もいなくなったら削除
            if not self.active_games[game_id]:
                del self.active_games[game_id]
        
        del self.connections[websocket]
        
        logger.info(f"Player {player_id} disconnected from game {game_id}")
        return game_id, player_id
    
    async def send_to_player(self, game_id: str, player_id: str, message: dict):
        """特定のプレイヤーにメッセージを送信"""
        if game_id in self.active_games and player_id in self.active_games[game_id]:
            websocket = self.active_games[game_id][player_id]
            await websocket.send_json(message)
    
    async def broadcast_to_game(self, game_id: str, message: dict, exclude_player: Optional[str] = None):
        """ゲーム内の全プレイヤーにメッセージをブロードキャスト"""
        if game_id not in self.active_games:
            return
        
        for player_id, websocket in self.active_games[game_id].items():
            if exclude_player and player_id == exclude_player:
                continue
            
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to player {player_id}: {e}")
    
    def get_game_players(self, game_id: str) -> List[str]:
        """ゲームに接続しているプレイヤーのリストを取得"""
        if game_id not in self.active_games:
            return []
        return list(self.active_games[game_id].keys())


# グローバルインスタンス
game_manager = GameConnectionManager()
