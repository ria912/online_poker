# リアルタイムチャットサービス

FastAPIとWebSocketを使用したリアルタイムチャットアプリケーションです。

## 機能

- ✅ リアルタイムメッセージング
- ✅ 複数チャットルーム対応
- ✅ ユーザー参加/退出通知
- ✅ タイピングインジケーター
- ✅ オンラインユーザー表示
- ✅ レスポンシブデザイン

## 必要な環境

- Python 3.8以上
- FastAPI
- Uvicorn
- WebSockets

## セットアップ

### 1. 依存関係のインストール

```powershell
cd c:\online_poker\server
pip install -r requirements.txt
```

### 2. サーバーの起動

```powershell
# serverディレクトリから実行
cd c:\online_poker\server
python main.py
```

または

```powershell
cd c:\online_poker\server
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 3. チャットアプリにアクセス

ブラウザで以下のURLにアクセス:
```
http://127.0.0.1:8000
```

## 使い方

1. **ユーザー名を入力**: チャットで表示される名前を入力します
2. **ルームIDを入力**: 同じルームIDを入力したユーザー同士でチャットできます
3. **参加する**: ボタンをクリックしてチャットルームに参加
4. **メッセージ送信**: 下部の入力欄からメッセージを送信できます

## 複数人でテストする方法

1. **同じパソコンで複数ウィンドウ**:
   - 複数のブラウザウィンドウ/タブで `http://127.0.0.1:8000` を開く
   - 各ウィンドウで異なるユーザー名を入力
   - 同じルームIDを入力して参加

2. **ネットワーク内の他のデバイス**:
   - サーバーを起動したPCのローカルIPアドレスを確認
   - 他のデバイスから `http://<ローカルIP>:8000` にアクセス

## プロジェクト構成

```
server/
├── main.py                          # FastAPIアプリケーションのエントリーポイント
├── app/
│   └── websocket/
│       ├── __init__.py              # WebSocketモジュール初期化
│       ├── chat_manager.py          # チャット接続管理
│       └── chat_routes.py           # WebSocketエンドポイント
└── requirements.txt                 # Python依存関係
```

## WebSocket API

### エンドポイント

```
ws://127.0.0.1:8000/ws/chat/{room_id}?username={username}
```

### メッセージ形式

**送信 (クライアント → サーバー)**:
```json
{
  "type": "message",
  "message": "こんにちは"
}
```

```json
{
  "type": "typing"
}
```

**受信 (サーバー → クライアント)**:

チャットメッセージ:
```json
{
  "type": "message",
  "username": "user1",
  "message": "こんにちは"
}
```

ユーザー参加:
```json
{
  "type": "user_joined",
  "username": "user1",
  "message": "user1 がルームに参加しました"
}
```

ユーザー退出:
```json
{
  "type": "user_left",
  "username": "user1",
  "message": "user1 がルームを退出しました"
}
```

ルーム情報:
```json
{
  "type": "room_info",
  "room_id": "room1",
  "users": ["user1", "user2"],
  "user_count": 2
}
```

タイピング通知:
```json
{
  "type": "typing",
  "username": "user1"
}
```

## カスタマイズ

### ポート番号の変更

`main.py` の最後の行を編集:
```python
uvicorn.run(app, host="127.0.0.1", port=8000)  # ポート番号を変更
```

### スタイルのカスタマイズ

`main.py` の `root()` 関数内のHTML/CSSを編集して、デザインをカスタマイズできます。

## トラブルシューティング

### ポートが既に使用されている

```powershell
# 別のポートを使用
python main.py  # コード内でポート番号を変更
# または
uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

### 接続エラー

- ファイアウォールの設定を確認
- サーバーが正しく起動しているか確認
- ブラウザのコンソールでエラーメッセージを確認

## 今後の拡張案

- [ ] メッセージ履歴の永続化
- [ ] プライベートメッセージ機能
- [ ] ファイル/画像の送信
- [ ] 絵文字/スタンプ
- [ ] ユーザー認証
- [ ] メッセージ検索
- [ ] 通知機能

## ライセンス

このプロジェクトは学習/開発用途で自由に使用できます。
