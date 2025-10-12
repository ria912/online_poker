from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from typing import Dict, List
import json
import asyncio

# WebSocketルーター
router = APIRouter()

# 接続管理
class ConnectionManager:
    """WebSocket接続管理クラス"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.game_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, game_id: str = None):
        """新しい接続を受け入れ"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if game_id:
            if game_id not in self.game_connections:
                self.game_connections[game_id] = []
            self.game_connections[game_id].append(websocket)
        
        print(f"新しい接続が確立されました。アクティブ接続数: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket, game_id: str = None):
        """接続を切断"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if game_id and game_id in self.game_connections:
            if websocket in self.game_connections[game_id]:
                self.game_connections[game_id].remove(websocket)
            
            # ゲームに接続がなくなったら削除
            if not self.game_connections[game_id]:
                del self.game_connections[game_id]
        
        print(f"接続が切断されました。アクティブ接続数: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """個別メッセージ送信"""
        await websocket.send_text(message)
    
    async def send_to_game(self, message: str, game_id: str):
        """ゲーム内全員にメッセージ送信"""
        if game_id in self.game_connections:
            for connection in self.game_connections[game_id]:
                try:
                    await connection.send_text(message)
                except:
                    # 切断された接続を削除
                    self.disconnect(connection, game_id)
    
    async def broadcast(self, message: str):
        """全接続にブロードキャスト"""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # 切断された接続を削除
                self.disconnect(connection)


# 接続マネージャーのインスタンス
manager = ConnectionManager()


@router.websocket("/game/{game_id}")
async def websocket_game_endpoint(websocket: WebSocket, game_id: str):
    """ゲーム用WebSocketエンドポイント"""
    await manager.connect(websocket, game_id)
    
    try:
        # 接続確認メッセージ
        await manager.send_personal_message(
            json.dumps({
                "type": "connection_established",
                "message": f"ゲーム {game_id} に接続しました",
                "game_id": game_id
            }),
            websocket
        )
        
        while True:
            # クライアントからのメッセージを待機
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                # メッセージタイプに応じた処理
                if message_type == "join_game":
                    player_name = message.get("player_name", "Anonymous")
                    response = {
                        "type": "player_joined",
                        "message": f"{player_name} がゲームに参加しました",
                        "player_name": player_name,
                        "game_id": game_id
                    }
                    await manager.send_to_game(json.dumps(response), game_id)
                
                elif message_type == "player_action":
                    action = message.get("action")
                    amount = message.get("amount")
                    response = {
                        "type": "action_received",
                        "message": f"アクション受信: {action}",
                        "action": action,
                        "amount": amount,
                        "game_id": game_id
                    }
                    await manager.send_to_game(json.dumps(response), game_id)
                
                elif message_type == "chat_message":
                    player_name = message.get("player_name", "Anonymous")
                    chat_message = message.get("message", "")
                    response = {
                        "type": "chat_message",
                        "player_name": player_name,
                        "message": chat_message,
                        "game_id": game_id
                    }
                    await manager.send_to_game(json.dumps(response), game_id)
                
                else:
                    # 不明なメッセージタイプ
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "error",
                            "message": f"不明なメッセージタイプ: {message_type}"
                        }),
                        websocket
                    )
            
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "無効なJSONフォーマットです"
                    }),
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, game_id)
        # 切断通知をゲーム内の他のプレイヤーに送信
        await manager.send_to_game(
            json.dumps({
                "type": "player_disconnected",
                "message": "プレイヤーが切断されました",
                "game_id": game_id
            }),
            game_id
        )


@router.websocket("/test")
async def websocket_test_endpoint(websocket: WebSocket):
    """WebSocket接続テスト用エンドポイント"""
    await manager.connect(websocket)
    
    try:
        await manager.send_personal_message(
            json.dumps({
                "type": "test_connection",
                "message": "WebSocket接続テストが成功しました"
            }),
            websocket
        )
        
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"エコー: {data}", websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)