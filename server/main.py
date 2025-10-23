"""
FastAPIアプリケーションのエントリーポイント
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.websocket import chat_router
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション作成
app = FastAPI(
    title="Real-time Chat Service",
    description="FastAPI + WebSocketを使用したリアルタイムチャットサービス",
    version="1.0.0"
)

# WebSocketルーターを追加
app.include_router(chat_router, tags=["WebSocket Chat"])

# 静的ファイルの提供
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """ルートエンドポイント - チャットクライアントのHTMLを返す"""
    return """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>リアルタイムチャット</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .container {
            width: 90%;
            max-width: 800px;
            height: 90vh;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .header {
            background: #667eea;
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 24px;
            margin-bottom: 5px;
        }
        
        .room-info {
            font-size: 14px;
            opacity: 0.9;
        }
        
        .login-screen {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 40px;
        }
        
        .login-screen input {
            width: 100%;
            max-width: 300px;
            padding: 15px;
            margin: 10px 0;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
        }
        
        .login-screen button {
            width: 100%;
            max-width: 300px;
            padding: 15px;
            margin-top: 10px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        .login-screen button:hover {
            background: #5568d3;
        }
        
        .chat-container {
            flex: 1;
            display: none;
            flex-direction: column;
        }
        
        .chat-container.active {
            display: flex;
        }
        
        .users-panel {
            background: #f8f9fa;
            padding: 15px;
            border-bottom: 1px solid #ddd;
        }
        
        .users-list {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .user-badge {
            background: #667eea;
            color: white;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 14px;
        }
        
        #messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #fafafa;
        }
        
        .message {
            margin-bottom: 15px;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .message.system {
            text-align: center;
            color: #666;
            font-style: italic;
            font-size: 14px;
        }
        
        .message.user .username {
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .message.user .content {
            background: white;
            padding: 10px 15px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .input-area {
            display: flex;
            gap: 10px;
            padding: 20px;
            background: white;
            border-top: 1px solid #ddd;
        }
        
        #messageInput {
            flex: 1;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
        }
        
        #sendButton {
            padding: 12px 30px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        #sendButton:hover {
            background: #5568d3;
        }
        
        .typing-indicator {
            padding: 10px 20px;
            color: #666;
            font-style: italic;
            font-size: 14px;
            min-height: 40px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💬 オンラインポーカー</h1>
            <div class="room-info" id="roomInfo">ロビー</div>
        </div>
        
        <div class="login-screen" id="loginScreen">
            <h2 style="margin-bottom: 30px;">ロビー</h2>
            <input type="text" id="usernameInput" placeholder="名前を入力してください" />
            <button onclick="enterLobby()">入室する</button>
        </div>
        
        <div class="chat-container" id="chatContainer">
            <div class="users-panel">
                <div style="font-weight: bold; margin-bottom: 10px;">参加者:</div>
                <div class="users-list" id="usersList"></div>
            </div>
            
            <div id="messages"></div>
            
            <div class="typing-indicator" id="typingIndicator"></div>
            
            <div class="input-area">
                <input 
                    type="text" 
                    id="messageInput" 
                    placeholder="メッセージを入力..."
                    onkeypress="handleKeyPress(event)"
                    oninput="handleTyping()"
                />
                <button id="sendButton" onclick="sendMessage()">送信</button>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let username = "";
        let roomId = "lobby"; // デフォルトでロビーに設定
        let typingTimeout = null;

        function enterLobby() {
            username = document.getElementById('usernameInput').value.trim();
            
            if (!username) {
                alert('名前を入力してください');
                return;
            }
            
            // WebSocket接続
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/chat/${roomId}?username=${encodeURIComponent(username)}`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function(event) {
                console.log('WebSocket接続成功');
                document.getElementById('loginScreen').style.display = 'none';
                document.getElementById('chatContainer').classList.add('active');
                document.getElementById('roomInfo').textContent = `ロビー | ${username}`;
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleMessage(data);
            };
            
            ws.onerror = function(error) {
                console.error('WebSocketエラー:', error);
                alert('接続エラーが発生しました');
            };
            
            ws.onclose = function(event) {
                console.log('WebSocket接続終了');
                addSystemMessage('接続が切断されました');
            };
        }
        
        function handleMessage(data) {
            switch(data.type) {
                case 'message':
                    addUserMessage(data.username, data.message);
                    break;
                case 'user_joined':
                    addSystemMessage(data.message);
                    break;
                case 'user_left':
                    addSystemMessage(data.message);
                    break;
                case 'room_info':
                    updateUsersList(data.users);
                    break;
                case 'typing':
                    if (data.username !== username) {
                        showTypingIndicator(data.username);
                    }
                    break;
            }
        }
        
        function addUserMessage(user, message) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message user';
            messageDiv.innerHTML = `
                <div class="username">${escapeHtml(user)}</div>
                <div class="content">${escapeHtml(message)}</div>
            `;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function addSystemMessage(message) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message system';
            messageDiv.textContent = message;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function updateUsersList(users) {
            const usersListDiv = document.getElementById('usersList');
            usersListDiv.innerHTML = users.map(user => 
                `<div class="user-badge">${escapeHtml(user)}</div>`
            ).join('');
        }
        
        function showTypingIndicator(user) {
            const indicator = document.getElementById('typingIndicator');
            indicator.textContent = `${user} が入力中...`;
            
            clearTimeout(typingTimeout);
            typingTimeout = setTimeout(() => {
                indicator.textContent = '';
            }, 2000);
        }
        
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (message && ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'message',
                    message: message
                }));
                input.value = '';
            }
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        function handleTyping() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'typing'
                }));
            }
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // ページを離れる際の確認
        window.addEventListener('beforeunload', function() {
            if (ws) {
                ws.close();
            }
        });
    </script>
</body>
</html>
    """


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy", "service": "chat"}


if __name__ == "__main__":
    import uvicorn
    # 0.0.0.0 にすることで、同じネットワーク内の他の端末からもアクセス可能になります
    uvicorn.run(app, host="0.0.0.0", port=8000)
