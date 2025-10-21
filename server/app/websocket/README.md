# WebSocket実装 - README

## 概要
リアルタイムポーカーゲーム用のWebSocket実装です。クライアントとサーバー間でゲーム状態の同期、プレイヤーアクション、イベント通知を行います。

## 構成

### ファイル構成
```
app/websocket/
├── __init__.py              # モジュール初期化
├── connection_manager.py    # WebSocket接続管理
└── router.py               # WebSocketエンドポイント
```

### 主要コンポーネント

#### 1. ConnectionManager (`connection_manager.py`)
WebSocket接続のライフサイクル管理:
- 接続の受け入れ・切断
- プレイヤーへの個別メッセージ送信
- ゲーム内全体へのブロードキャスト

#### 2. WebSocketRouter (`router.py`)
WebSocketエンドポイントとメッセージハンドラー:
- クライアントメッセージの受信・処理
- ゲーム状態のシリアライズ
- プレイヤー視点の情報フィルタリング

## エンドポイント

### WebSocket URL
```
ws://localhost:8000/ws/game/{game_id}/{player_id}
```

**パラメータ:**
- `game_id`: ゲームID（例: "game_123", "test_game"）
- `player_id`: プレイヤーID（例: "player1", "alice_001"）

## メッセージ仕様

### クライアント → サーバー

#### 1. ゲーム参加
```json
{
  "type": "join_game",
  "player_name": "Alice",
  "buy_in": 10000
}
```

#### 2. ゲーム開始
```json
{
  "type": "start_game"
}
```

#### 3. プレイヤーアクション
```json
{
  "type": "player_action",
  "action_type": "CALL",
  "amount": 100
}
```

**action_type 一覧:**
- `FOLD`: 降りる
- `CHECK`: チェック
- `CALL`: コール
- `BET`: ベット（amountが必要）
- `RAISE`: レイズ（amountが必要）
- `ALL_IN`: オールイン

#### 4. 状態取得
```json
{
  "type": "get_state"
}
```

### サーバー → クライアント

#### 1. 接続成功
```json
{
  "type": "connected",
  "game_id": "game_1",
  "player_id": "player1"
}
```

#### 2. ゲーム状態更新
```json
{
  "type": "game_state_update",
  "game_state": {
    "id": "game_1",
    "status": "IN_PROGRESS",
    "current_round": "FLOP",
    "current_bet": 200,
    "total_pot": 500,
    "community_cards": ["Ah", "Kd", "Qs"],
    "seats": [...]
  },
  "your_seat_index": 0,
  "valid_actions": ["FOLD", "CALL", "RAISE"],
  "is_your_turn": true
}
```

#### 3. プレイヤー参加通知
```json
{
  "type": "player_joined",
  "player_id": "player2",
  "player_name": "Bob"
}
```

#### 4. ゲーム開始通知
```json
{
  "type": "game_started",
  "message": "Game has started!"
}
```

#### 5. アクション結果
```json
{
  "type": "action_result",
  "success": true,
  "message": "Action CALL processed"
}
```

#### 6. エラー通知
```json
{
  "type": "error",
  "message": "Invalid action"
}
```

#### 7. プレイヤー切断通知
```json
{
  "type": "player_disconnected",
  "player_id": "player2"
}
```

## 使用方法

### サーバー起動
```bash
cd server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### テストクライアント使用

1. ブラウザで `test_websocket_client.html` を開く
2. Game ID とPlayer IDを入力（例: "test_game", "player1"）
3. "Connect"ボタンをクリック
4. "Join Game"でゲームに参加
5. 別のブラウザで同じGame IDに別のPlayer IDで接続
6. どちらかのクライアントで"Start Game"をクリック
7. 順番にアクションを実行してゲームを進行

### Pythonクライアント例
```python
import asyncio
import websockets
import json

async def poker_client():
    uri = "ws://localhost:8000/ws/game/test_game/player1"
    
    async with websockets.connect(uri) as websocket:
        # ゲーム参加
        await websocket.send(json.dumps({
            "type": "join_game",
            "player_name": "Alice",
            "buy_in": 10000
        }))
        
        # メッセージ受信ループ
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Received: {data}")
            
            # ゲーム状態更新時の処理
            if data["type"] == "game_state_update":
                if data.get("is_your_turn"):
                    # 自分のターン: アクション送信
                    valid_actions = data.get("valid_actions", [])
                    if "CHECK" in valid_actions:
                        await websocket.send(json.dumps({
                            "type": "player_action",
                            "action_type": "CHECK"
                        }))

asyncio.run(poker_client())
```

## 設計の特徴

### 1. プレイヤー視点の情報フィルタリング
- ホールカードは本人にのみ表示（ショーダウン時を除く）
- 各プレイヤーに個別のゲーム状態を送信
- 有効なアクションリストは自分のターン時のみ

### 2. 自動ブロードキャスト
- アクション実行後、全プレイヤーにゲーム状態を自動送信
- プレイヤー参加/切断を全員に通知
- ゲーム進行イベントをリアルタイム配信

### 3. エラーハンドリング
- 無効なアクションをエラーメッセージで通知
- 接続切断を検知して自動クリーンアップ
- 送信失敗時の再試行とロギング

## 今後の拡張

### 優先度: 高
- [ ] 切断プレイヤーの自動フォールド処理
- [ ] タイムアウト機能（30秒で自動アクション）
- [ ] 観戦モード（プレイせず状態を見るだけ）

### 優先度: 中
- [ ] チャット機能
- [ ] プレイヤー統計のリアルタイム更新
- [ ] リプレイ/履歴機能

### 優先度: 低
- [ ] 複数テーブル対応
- [ ] ロビーシステム
- [ ] トーナメント管理

## トラブルシューティング

### 接続できない
- サーバーが起動しているか確認: `http://localhost:8000/health`
- CORS設定を確認（ブラウザのコンソールをチェック）
- ファイアウォール設定を確認

### メッセージが受信できない
- WebSocketの接続状態を確認
- ブラウザのコンソールでエラーログをチェック
- サーバーログで送信エラーを確認

### ゲームが進まない
- 現在のアクター（your_turn）を確認
- 有効なアクション（valid_actions）を確認
- ゲーム状態（status, current_round）を確認

## 参考資料
- [FastAPI WebSocket Documentation](https://fastapi.tiangolo.com/advanced/websockets/)
- [WebSocket API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
