"""
WebSocketチャット接続を管理するマネージャー
"""
from typing import Dict, Set
from fastapi import WebSocket


class ChatConnectionManager:
    """WebSocket接続を管理するクラス"""
    
    def __init__(self):
        # アクティブな接続を保持する辞書 {room_id: set of websockets}
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # ユーザー名を保持する辞書 {websocket: username}
        self.usernames: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, room_id: str, username: str):
        """WebSocket接続を受け入れ、ルームに追加"""
        await websocket.accept()
        
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        
        self.active_connections[room_id].add(websocket)
        self.usernames[websocket] = username
        
        # 接続通知をルーム内の全員に送信
        await self.broadcast(
            room_id,
            {
                "type": "user_joined",
                "username": username,
                "message": f"{username} がルームに参加しました"
            }
        )
    
    def disconnect(self, websocket: WebSocket, room_id: str):
        """WebSocket接続を切断"""
        username = self.usernames.get(websocket, "Unknown")
        
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)
            
            # ルームが空になったら削除
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        
        if websocket in self.usernames:
            del self.usernames[websocket]
        
        return username
    
    async def broadcast(self, room_id: str, message: dict):
        """特定のルーム内の全接続にメッセージを送信"""
        if room_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            
            # 切断されたコネクションを削除
            for conn in disconnected:
                self.active_connections[room_id].discard(conn)
                if conn in self.usernames:
                    del self.usernames[conn]
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """特定の接続にメッセージを送信"""
        try:
            await websocket.send_json(message)
        except Exception:
            pass
    
    def get_room_users(self, room_id: str) -> list:
        """ルーム内のユーザー一覧を取得"""
        if room_id not in self.active_connections:
            return []
        
        return [
            self.usernames.get(ws, "Unknown")
            for ws in self.active_connections[room_id]
        ]


# グローバルインスタンス
chat_manager = ChatConnectionManager()
