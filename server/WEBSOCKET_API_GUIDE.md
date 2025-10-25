# WebSocket & API 実装ガイド

## 概要

ベストプラクティスに沿って、ゲーム進行に集中したWebSocketとREST APIを実装しました。

## アーキテクチャ

```
app/
├── api/                      # REST API
│   ├── game_api.py          # ゲーム作成・管理エンドポイント
│   └── __init__.py
│
├── websocket/                # WebSocket
│   ├── connection_manager.py # 接続管理（シングルトン）
│   ├── serializers.py        # ゲーム状態のシリアライズ
│   ├── routes.py             # WebSocketエンドポイント
│   └── __init__.py
│
└── game/                     # ゲームロジック
    ├── domain/               # ドメインモデル
    ├── services/             # ビジネスロジック
    └── logic/                # ゲームルール
```

## 使用方法

### 1. サーバー起動

```bash
cd c:\online_poker\server
python main.py
```

サーバーは http://0.0.0.0:8000 で起動します

### 2. API ドキュメント

自動生成されたAPIドキュメントにアクセス:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. ゲームフロー

#### Step 1: ゲーム作成（REST API）

```bash
POST http://localhost:8000/api/games/single-play
Content-Type: application/json

{
  "big_blind": 100,
  "buy_in": 10000
}
```

**レスポンス:**
```json
{
  "game_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Single play game created successfully",
  "ai_players": ["AI_Player_1", "AI_Player_2"],
  "websocket_url": "/ws/game/550e8400-e29b-41d4-a716-446655440000?username=YOUR_USERNAME"
}
```

#### Step 2: WebSocket接続

```javascript
const ws = new WebSocket(
  'ws://localhost:8000/ws/game/YOUR_GAME_ID?username=Player1'
);

ws.onopen = () => {
  console.log('Connected');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};
```

#### Step 3: ゲーム開始

```javascript
ws.send(JSON.stringify({
  type: 'start_game'
}));
```

#### Step 4: アクション実行

```javascript
// コール
ws.send(JSON.stringify({
  type: 'player_action',
  action: 'CALL',
  amount: 100
}));

// チェック
ws.send(JSON.stringify({
  type: 'player_action',
  action: 'CHECK',
  amount: 0
}));

// フォールド
ws.send(JSON.stringify({
  type: 'player_action',
  action: 'FOLD',
  amount: 0
}));
```

## メッセージフォーマット

### クライアント → サーバー

#### ゲーム開始
```json
{
  "type": "start_game"
}
```

#### プレイヤーアクション
```json
{
  "type": "player_action",
  "action": "CALL" | "CHECK" | "FOLD" | "BET" | "RAISE",
  "amount": 100
}
```

#### 状態取得
```json
{
  "type": "get_state"
}
```

### サーバー → クライアント

#### 接続完了
```json
{
  "type": "connected",
  "data": {
    "player_id": "uuid",
    "game_id": "uuid",
    "message": "Welcome Player1!"
  }
}
```

#### ゲーム状態
```json
{
  "type": "game_state",
  "data": {
    "game_id": "uuid",
    "status": "IN_PROGRESS",
    "current_round": "FLOP",
    "current_seat_index": 0,
    "current_bet": 100,
    "small_blind": 50,
    "big_blind": 100,
    "dealer_seat_index": 2,
    "seats": [
      {
        "index": 0,
        "player": {
          "id": "uuid",
          "name": "Player1",
          "is_ai": false
        },
        "stack": 9900,
        "status": "ACTIVE",
        "bet_in_round": 100,
        "bet_in_hand": 100,
        "hole_cards": [
          {"rank": "A", "suit": "♠"},
          {"rank": "K", "suit": "♥"}
        ],
        "last_action": "CALL",
        "position": "BTN"
      }
    ],
    "community_cards": [
      {"rank": "Q", "suit": "♦"},
      {"rank": "J", "suit": "♣"},
      {"rank": "10", "suit": "♠"}
    ],
    "pots": [
      {
        "amount": 300,
        "eligible_player_ids": ["uuid1", "uuid2", "uuid3"]
      }
    ],
    "winners": [],
    "valid_actions": []
  }
}
```

#### エラー
```json
{
  "type": "error",
  "data": null,
  "error": "Invalid action"
}
```

## ベストプラクティス

### 1. 関心の分離
- **REST API**: ゲーム作成・削除などの単発操作
- **WebSocket**: リアルタイムなゲーム進行

### 2. 接続管理
- `ConnectionManager`: シングルトンパターンで一元管理
- 自動切断処理とクリーンアップ

### 3. セキュリティ
- プレイヤーごとにホールカードの表示制御
- WebSocket接続時にゲーム存在確認
- CORS設定で開発環境を許可

### 4. エラーハンドリング
- 適切なHTTPステータスコード使用
- 詳細なログ出力
- クライアントへのエラーメッセージ送信

### 5. AI自動処理
- AIのターンを自動検出して処理
- 無限ループ防止（最大10イテレーション）
- 1.5秒の遅延でリアルな体験

## テスト

### curlでのテスト

```bash
# ヘルスチェック
curl http://localhost:8000/health

# API情報
curl http://localhost:8000/api/info

# ゲーム作成
curl -X POST http://localhost:8000/api/games/single-play \
  -H "Content-Type: application/json" \
  -d '{"big_blind": 100, "buy_in": 10000}'

# ゲーム情報取得
curl http://localhost:8000/api/games/YOUR_GAME_ID
```

### WebSocketテスト（JavaScript）

```html
<!DOCTYPE html>
<html>
<head>
    <title>Poker Test</title>
</head>
<body>
    <h1>Poker Game Test</h1>
    <div id="log"></div>
    
    <script>
        const gameId = 'YOUR_GAME_ID';
        const ws = new WebSocket(`ws://localhost:8000/ws/game/${gameId}?username=TestPlayer`);
        
        const log = document.getElementById('log');
        
        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            log.innerHTML += `<pre>${JSON.stringify(msg, null, 2)}</pre>`;
            
            // 自動でゲーム開始
            if (msg.type === 'connected') {
                setTimeout(() => {
                    ws.send(JSON.stringify({type: 'start_game'}));
                }, 1000);
            }
        };
        
        ws.onerror = (error) => {
            log.innerHTML += `<p style="color:red">Error: ${error}</p>`;
        };
        
        // アクション送信ボタン
        window.call = () => {
            ws.send(JSON.stringify({
                type: 'player_action',
                action: 'CALL',
                amount: 0
            }));
        };
        
        window.check = () => {
            ws.send(JSON.stringify({
                type: 'player_action',
                action: 'CHECK',
                amount: 0
            }));
        };
        
        window.fold = () => {
            ws.send(JSON.stringify({
                type: 'player_action',
                action: 'FOLD',
                amount: 0
            }));
        };
    </script>
    
    <button onclick="call()">Call</button>
    <button onclick="check()">Check</button>
    <button onclick="fold()">Fold</button>
</body>
</html>
```

## トラブルシューティング

### WebSocket接続失敗

1. ゲームIDが正しいか確認
2. ゲームが存在するか確認（GET /api/games/{game_id}）
3. usernameパラメータが指定されているか確認

### AIが動作しない

1. ゲームが開始されているか確認（status: IN_PROGRESS）
2. ログを確認してエラーを特定
3. AI判定ロジック（player.is_ai）を確認

### メッセージが受信できない

1. WebSocket接続が確立されているか確認
2. ブラウザの開発者ツールでネットワークタブを確認
3. サーバーログでエラーを確認

## まとめ

このアーキテクチャの利点:

✅ **明確な責務分離**: REST APIとWebSocketの役割が明確
✅ **スケーラブル**: ConnectionManagerで複数ゲームの同時管理
✅ **保守性**: 各モジュールが独立しており、テスト・修正が容易
✅ **セキュリティ**: プレイヤーごとの情報制御
✅ **リアルタイム**: AIの自動処理でスムーズなゲーム進行

チャット機能を削除し、ゲーム進行に集中した設計により、コードベースがシンプルで理解しやすくなりました。
