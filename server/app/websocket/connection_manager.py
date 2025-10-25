"""
WebSocket接続管理
接続の追加・削除・メッセージ送信を一元管理
"""
from fastapi import WebSocket
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket接続を管理するクラス"""
    
    def __init__(self):
        # game_id -> {player_id: websocket}
        self._connections: Dict[str, Dict[str, WebSocket]] = {}
        # websocket -> (game_id, player_id)
        self._reverse_lookup: Dict[WebSocket, tuple[str, str]] = {}
    
    async def connect(self, websocket: WebSocket, game_id: str, player_id: str) -> None:
        """
        プレイヤーをゲームに接続
        
        Args:
            websocket: WebSocket接続
            game_id: ゲームID
            player_id: プレイヤーID
        """
        await websocket.accept()
        
        if game_id not in self._connections:
            self._connections[game_id] = {}
        
        self._connections[game_id][player_id] = websocket
        self._reverse_lookup[websocket] = (game_id, player_id)
        
        logger.info(f"Player {player_id} connected to game {game_id}")
    
    def disconnect(self, websocket: WebSocket) -> Optional[tuple[str, str]]:
        """
        接続を切断
        
        Args:
            websocket: WebSocket接続
            
        Returns:
            Optional[tuple]: (game_id, player_id) または None
        """
        if websocket not in self._reverse_lookup:
            return None
        
        game_id, player_id = self._reverse_lookup[websocket]
        
        # 接続情報を削除
        if game_id in self._connections:
            self._connections[game_id].pop(player_id, None)
            
            # ゲームに誰もいなくなったら削除
            if not self._connections[game_id]:
                del self._connections[game_id]
        
        del self._reverse_lookup[websocket]
        
        logger.info(f"Player {player_id} disconnected from game {game_id}")
        return game_id, player_id
    
    async def send_personal(self, game_id: str, player_id: str, message: dict) -> bool:
        """
        特定のプレイヤーにメッセージを送信
        
        Args:
            game_id: ゲームID
            player_id: プレイヤーID
            message: 送信するメッセージ
            
        Returns:
            bool: 送信成功したらTrue
        """
        if game_id not in self._connections or player_id not in self._connections[game_id]:
            logger.warning(f"Player {player_id} not found in game {game_id}")
            return False
        
        try:
            websocket = self._connections[game_id][player_id]
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.error(f"Error sending message to player {player_id}: {e}")
            return False
    
    async def broadcast(self, game_id: str, message: dict, exclude: Optional[str] = None) -> int:
        """
        ゲーム内の全プレイヤーにメッセージをブロードキャスト
        
        Args:
            game_id: ゲームID
            message: 送信するメッセージ
            exclude: 除外するプレイヤーID
            
        Returns:
            int: 送信成功したプレイヤー数
        """
        if game_id not in self._connections:
            logger.warning(f"Game {game_id} not found in connections")
            return 0
        
        success_count = 0
        for player_id, websocket in self._connections[game_id].items():
            if exclude and player_id == exclude:
                continue
            
            try:
                await websocket.send_json(message)
                success_count += 1
            except Exception as e:
                logger.error(f"Error broadcasting to player {player_id}: {e}")
        
        return success_count
    
    def is_connected(self, game_id: str, player_id: str) -> bool:
        """
        プレイヤーが接続されているかチェック
        
        Args:
            game_id: ゲームID
            player_id: プレイヤーID
            
        Returns:
            bool: 接続されていればTrue
        """
        return (game_id in self._connections and 
                player_id in self._connections[game_id])
    
    def get_connected_players(self, game_id: str) -> list[str]:
        """
        ゲームに接続中のプレイヤーIDリストを取得
        
        Args:
            game_id: ゲームID
            
        Returns:
            list[str]: プレイヤーIDのリスト
        """
        if game_id not in self._connections:
            return []
        return list(self._connections[game_id].keys())


# グローバルインスタンス
connection_manager = ConnectionManager()
