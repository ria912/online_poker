# Online Poker Game

FastAPI + React + TypeScript + WebSocketを使用したオンラインポーカーゲーム

## プロジェクト構成

```
online_poker/
├── client/          # React + TypeScript + Vite フロントエンド
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
└── server/          # FastAPI バックエンド
    ├── app/
    │   ├── websocket/
    │   ├── game/
    │   └── core/
    ├── main.py
    └── requirements.txt
```

## セットアップ

### サーバー側（FastAPI）

1. Pythonの仮想環境を作成して有効化

```powershell
cd server
python -m venv venv
.\venv\Scripts\Activate
```

2. 依存パッケージをインストール

```powershell
pip install -r requirements.txt
```

3. サーバーを起動

```powershell
python main.py
```

サーバーは `http://localhost:8000` で起動します。

### クライアント側（React + Vite）

1. 依存パッケージをインストール

```powershell
cd client
npm install
```

2. 開発サーバーを起動

```powershell
npm run dev
```

クライアントは `http://localhost:5173` で起動します。

## 開発モード

開発時は以下の2つのサーバーを同時に起動します:

1. **バックエンドサーバー** (`http://localhost:8000`)
   - API エンドポイント
   - WebSocket エンドポイント

2. **フロントエンドサーバー** (`http://localhost:5173`)
   - React 開発サーバー（Hot Reload対応）

## 本番ビルド

1. クライアントをビルド

```powershell
cd client
npm run build
```

2. サーバーを起動

```powershell
cd ..\server
python main.py
```

本番モードでは、FastAPIサーバーが `http://localhost:8000` でReactアプリとAPIの両方を提供します。

## API エンドポイント

### REST API

- `GET /health` - ヘルスチェック
- `GET /api/info` - API情報

### WebSocket

- `WS /ws/chat/{room_id}` - チャット用WebSocket接続

## 技術スタック

### フロントエンド

- React 18
- TypeScript
- Vite
- CSS Modules / Styled Components

### バックエンド

- FastAPI
- WebSocket
- Pydantic
- Uvicorn

## 開発Tips

### CORS設定

開発時は`main.py`でCORS設定により、`http://localhost:5173`からのアクセスが許可されています。

### ホットリロード

- フロントエンド: Viteが自動的にファイル変更を検知
- バックエンド: `uvicorn.run()`の`reload=True`オプションで有効化可能

### WebSocket接続

開発時は `ws://localhost:8000/ws/chat/{room_id}` に接続します。

## トラブルシューティング

### ポートが使用中の場合

```powershell
# ポート8000を使用しているプロセスを確認
netstat -ano | findstr :8000

# プロセスを終了
taskkill /PID <プロセスID> /F
```

### CORSエラーが発生する場合

`server/main.py`の`allow_origins`にフロントエンドのURLが含まれているか確認してください。
