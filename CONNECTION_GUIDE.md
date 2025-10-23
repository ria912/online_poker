# クライアントとサーバーの接続方法

## 🚀 起動手順

### 1. サーバー起動（ターミナル1）

```powershell
# サーバーディレクトリに移動
cd C:\online_poker\server

# 仮想環境を有効化（初回のみ作成）
python -m venv venv
.\venv\Scripts\Activate

# 依存パッケージをインストール（初回のみ）
pip install -r requirements.txt

# サーバー起動
python main.py
```

✅ サーバーが `http://localhost:8000` で起動します

### 2. クライアント起動（ターミナル2）

```powershell
# クライアントディレクトリに移動
cd C:\online_poker\client

# 依存パッケージをインストール（初回のみ）
npm install

# 開発サーバー起動
npm run dev
```

✅ クライアントが `http://localhost:5173` で起動します

### 3. ブラウザでアクセス

ブラウザで `http://localhost:5173` を開く

---

## 🔌 WebSocket接続の仕組み

### エンドポイント

#### チャット用
```
ws://localhost:8000/ws/chat/{room_id}?username=ユーザー名
```

#### ゲーム用
```
ws://localhost:8000/ws/game/{game_id}?username=ユーザー名
```

### 接続フロー

1. **クライアント側**: `useGameWebSocket` フックを使用
2. **サーバー側**: FastAPIのWebSocketエンドポイントで受信
3. **双方向通信**: JSON形式でメッセージを送受信

---

## 📡 メッセージフォーマット

### クライアント → サーバー

#### プレイヤーアクション
```typescript
{
  type: 'action',
  action: 'fold' | 'check' | 'call' | 'raise' | 'allin',
  amount: 100  // raiseの場合のみ
}
```

#### チャットメッセージ
```typescript
{
  type: 'chat',
  message: 'Hello!'
}
```

#### ゲーム状態リクエスト
```typescript
{
  type: 'get_state'
}
```

### サーバー → クライアント

#### 接続確認
```json
{
  "type": "connected",
  "message": "ゲームに接続しました",
  "game_id": "single-player-1",
  "player_id": "username"
}
```

#### ゲーム状態更新
```json
{
  "type": "game_state",
  "state": {
    "players": [...],
    "communityCards": [...],
    "pot": 100,
    "currentPlayerIndex": 0,
    "phase": "preflop"
  }
}
```

#### プレイヤーアクション通知
```json
{
  "type": "player_action",
  "username": "Player1",
  "action": "raise",
  "amount": 50
}
```

#### チャットメッセージ
```json
{
  "type": "chat",
  "username": "Player1",
  "message": "Good game!"
}
```

---

## 🧪 動作確認方法

### 1. 接続テスト

1. ブラウザで `http://localhost:5173` を開く
2. 名前を入力して「入室する」をクリック
3. 「ゲーム開始」をクリック
4. ブラウザの開発者ツール（F12）を開く
5. Consoleタブで以下のログを確認:
   ```
   WebSocket connected: ws://localhost:8000/ws/game/single-player-1?username=...
   Game WebSocket opened
   Received message: { type: 'connected', ... }
   ```

### 2. アクション送信テスト

1. ゲーム画面で「チェック」ボタンをクリック
2. Consoleで以下を確認:
   ```
   Action: check
   Received message: { type: 'player_action', action: 'check', ... }
   ```

### 3. 複数タブでテスト

1. 同じブラウザで2つのタブを開く
2. 両方で同じゲームに参加
3. 一方のタブでアクションを実行
4. もう一方のタブで通知を受信することを確認

---

## 🐛 トラブルシューティング

### WebSocket接続エラー

**問題**: `WebSocket connection failed`

**解決策**:
1. サーバーが起動しているか確認
2. ポート8000が使用可能か確認
3. CORSエラーの場合、`server/main.py`のCORS設定を確認

### サーバーが起動しない

**問題**: `ModuleNotFoundError`

**解決策**:
```powershell
cd server
pip install -r requirements.txt
```

### クライアントが起動しない

**問題**: `npm ERR!`

**解決策**:
```powershell
cd client
rm -r node_modules
npm install
```

---

## 📊 開発者ツールでの確認

### Networkタブ

1. F12で開発者ツールを開く
2. Networkタブを選択
3. 「WS」フィルタをクリック
4. WebSocket接続を確認

### 送受信メッセージの確認

1. WebSocket接続をクリック
2. Messagesタブで送受信履歴を確認
3. Framesタブで詳細を確認

---

## 🔧 設定ファイル

### サーバー側: `server/main.py`

```python
# CORS設定
allow_origins=[
    "http://localhost:5173",  # Viteデフォルトポート
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
```

### クライアント側: `client/src/hooks/useGameWebSocket.ts`

```typescript
// WebSocket URL構築
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/game/${gameId}?username=${encodeURIComponent(username)}`;
```

---

## ✅ チェックリスト

- [ ] サーバーが `http://localhost:8000` で起動している
- [ ] クライアントが `http://localhost:5173` で起動している
- [ ] ブラウザでクライアントにアクセスできる
- [ ] 名前を入力してロビーに入室できる
- [ ] ゲームを開始できる
- [ ] ブラウザのConsoleでWebSocket接続ログが表示される
- [ ] アクションボタンをクリックするとメッセージが送信される

---

## 🎯 次のステップ

現在の実装状況:
- ✅ WebSocket接続
- ✅ メッセージ送受信
- ✅ UI表示
- ⏳ ゲームロジック（未実装）
- ⏳ AI実装（未実装）

次に実装すべき機能:
1. サーバー側のゲームロジック（カード配布、ベッティング）
2. AI プレイヤーの実装
3. ハンド評価と勝者判定
4. ポット配分
