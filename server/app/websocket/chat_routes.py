"""
WebSocketチャットのエンドポイント
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from .chat_manager import chat_manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/chat/{room_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    room_id: str,
    username: str = Query(..., description="ユーザー名")
):
    """
    WebSocketチャットエンドポイント
    
    Args:
        websocket: WebSocket接続
        room_id: チャットルームID
        username: ユーザー名
    """
    await chat_manager.connect(websocket, room_id, username)
    logger.info(f"User {username} connected to room {room_id}")
    
    # 現在のルームメンバーを送信
    room_users = chat_manager.get_room_users(room_id)
    await chat_manager.send_personal_message(
        {
            "type": "room_info",
            "room_id": room_id,
            "users": room_users,
            "user_count": len(room_users)
        },
        websocket
    )
    
    try:
        while True:
            # クライアントからのメッセージを受信
            data = await websocket.receive_json()
            
            message_type = data.get("type", "message")
            message_content = data.get("message", "")
            
            if message_type == "message":
                # チャットメッセージをルーム内にブロードキャスト
                await chat_manager.broadcast(
                    room_id,
                    {
                        "type": "message",
                        "username": username,
                        "message": message_content
                    }
                )
            elif message_type == "typing":
                # タイピング中の通知
                await chat_manager.broadcast(
                    room_id,
                    {
                        "type": "typing",
                        "username": username
                    }
                )
            
    except WebSocketDisconnect:
        # 接続が切断された場合
        disconnected_user = chat_manager.disconnect(websocket, room_id)
        logger.info(f"User {disconnected_user} disconnected from room {room_id}")
        
        # 切断通知をルーム内の残りのユーザーに送信
        await chat_manager.broadcast(
            room_id,
            {
                "type": "user_left",
                "username": disconnected_user,
                "message": f"{disconnected_user} がルームを退出しました"
            }
        )
    except Exception as e:
        logger.error(f"Error in chat websocket: {e}")
        chat_manager.disconnect(websocket, room_id)
