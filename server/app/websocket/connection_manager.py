"""WebSocket接続管理"""
from typing import Dict, List, Optional
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket接続を管理するクラス"""
    
    def __init__(self):
        # game_id -> {player_id -> WebSocket}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, game_id: str, player_id: str):
        """WebSocket接続を受け入れる"""
        await websocket.accept()
        
        if game_id not in self.active_connections:
            self.active_connections[game_id] = {}
        
        self.active_connections[game_id][player_id] = websocket
        logger.info(f"Player {player_id} connected to game {game_id}")
    
    def disconnect(self, game_id: str, player_id: str):
        """WebSocket接続を切断する"""
        if game_id in self.active_connections:
            self.active_connections[game_id].pop(player_id, None)
            
            # ゲームに誰もいなくなったら削除
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]
        
        logger.info(f"Player {player_id} disconnected from game {game_id}")
    
    async def send_personal_message(self, message: dict, game_id: str, player_id: str):
        """特定のプレイヤーにメッセージを送信"""
        if game_id in self.active_connections:
            if player_id in self.active_connections[game_id]:
                websocket = self.active_connections[game_id][player_id]
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message to {player_id}: {e}")
    
    async def broadcast_to_game(self, message: dict, game_id: str, exclude_player: Optional[str] = None):
        """ゲーム内の全プレイヤーにメッセージをブロードキャスト"""
        if game_id not in self.active_connections:
            return
        
        disconnected_players = []
        
        for player_id, websocket in self.active_connections[game_id].items():
            if exclude_player and player_id == exclude_player:
                continue
            
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to {player_id}: {e}")
                disconnected_players.append(player_id)
        
        # 切断されたプレイヤーを削除
        for player_id in disconnected_players:
            self.disconnect(game_id, player_id)
    
    def get_connected_players(self, game_id: str) -> List[str]:
        """ゲームに接続中のプレイヤーIDリストを取得"""
        if game_id in self.active_connections:
            return list(self.active_connections[game_id].keys())
        return []


# グローバルインスタンス
manager = ConnectionManager()
