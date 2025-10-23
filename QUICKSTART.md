# 🎮 オンラインポーカー - クイックスタート

## 最速で動かす方法（3ステップ）

### ステップ1: サーバー起動
```powershell
cd C:\online_poker\server
python main.py
```

### ステップ2: クライアント起動（別のターミナル）
```powershell
cd C:\online_poker\client
npm run dev
```

### ステップ3: ブラウザでアクセス
`http://localhost:5173` を開く

---

## ✨ 使い方

1. **名前を入力** → 「入室する」
2. **シングルプレイ** → 「ゲーム開始」
3. **ゲームプレイ** → アクションボタンでプレイ

---

## 🔍 動作確認

### WebSocket接続を確認

1. ブラウザで F12（開発者ツール）
2. Console タブを確認
3. 以下のログが表示されればOK:
   ```
   WebSocket connected: ws://localhost:8000/ws/game/...
   Game WebSocket opened
   Received message: { type: 'connected', ... }
   ```

### アクション送信を確認

1. ゲーム画面で「チェック」をクリック
2. Consoleで `Action: check` と表示
3. `Received message: { type: 'player_action', ... }` と表示

---

## 📁 主要ファイル

### サーバー側
- `server/main.py` - FastAPIアプリケーション
- `server/app/websocket/game_routes.py` - ゲーム用WebSocket
- `server/app/websocket/game_manager.py` - 接続管理

### クライアント側
- `client/src/App.tsx` - ルーティング
- `client/src/pages/GamePage.tsx` - ゲーム画面
- `client/src/hooks/useGameWebSocket.ts` - WebSocket接続

---

## 🐛 問題が起きたら

### サーバーエラー
```powershell
cd server
pip install -r requirements.txt
python main.py
```

### クライアントエラー
```powershell
cd client
npm install
npm run dev
```

### ポート競合
```powershell
# ポート8000を使用しているプロセスを確認
netstat -ano | findstr :8000
# プロセスを終了
taskkill /PID <プロセスID> /F
```

---

## 📖 詳細ドキュメント

- 📘 **接続の詳細**: `CONNECTION_GUIDE.md`
- 📗 **プロジェクト概要**: `README.md`
- 📙 **クライアント詳細**: `client/CLIENT_README.md`

---

## 🎯 現在の状態

- ✅ WebSocket接続
- ✅ UI表示
- ✅ メッセージ送受信
- ⏳ ゲームロジック（次のステップ）
- ⏳ AI実装（次のステップ）
