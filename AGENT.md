# Online Poker Game - エージェント開発ガイド

## プロジェクト概要

### 最終目標
- **マルチプレイヤーオンラインポーカーゲーム**の実装
- リアルタイム対戦機能
- 複数のゲームルーム対応
- ランキング・統計機能

### 現在の目標
- **シングルプレイポーカーゲーム**の実装
- プレイヤー vs AI の対戦
- テキサスホールデムルール
- 基本的なゲームフロー

## 技術スタック

### バックエンド (`server/`)
- **FastAPI**: REST API & WebSocket通信
- **Python 3.11+**: メイン開発言語
- **SQLAlchemy**: ORM（データベース操作）
- **SQLite**: 開発環境用DB
- **PostgreSQL**: 本番環境用DB
- **WebSocket**: リアルタイム通信

### フロントエンド (`client/`)
- **React**: UIフレームワーク
- **TypeScript**: 型安全性確保
- **Material-UI (MUI)**: UIコンポーネント
- **Vite**: ビルドツール・開発サーバー
- **WebSocket**: サーバーとの通信

## プロジェクト構造

```
online_poker/
├── server/                    # バックエンド
│   ├── app/                   # アプリケーションコード
│   │   ├── api/              # API エンドポイント
│   │   ├── core/             # 設定・セキュリティ
│   │   ├── models/           # データベースモデル
│   │   ├── schemas/          # Pydanticスキーマ
│   │   ├── services/         # ビジネスロジック
│   │   ├── game/             # ゲームロジック
│   │   │   ├── poker.py      # ポーカーゲームエンジン
│   │   │   ├── ai.py         # AIロジック
│   │   │   └── rules.py      # ゲームルール
│   │   └── websocket/        # WebSocket処理
│   ├── tests/                # テストコード
│   ├── alembic/              # DBマイグレーション
│   ├── requirements.txt      # 依存関係
│   └── main.py               # アプリケーションエントリポイント
├── client/                    # フロントエンド
│   ├── src/
│   │   ├── components/       # Reactコンポーネント
│   │   ├── pages/            # ページコンポーネント
│   │   ├── hooks/            # カスタムフック
│   │   ├── types/            # TypeScript型定義
│   │   ├── services/         # API通信
│   │   └── utils/            # ユーティリティ
│   ├── public/               # 静的ファイル
│   └── package.json          # 依存関係
└── AGENT.md                  # このファイル
```

## 現在の実装フェーズ

### Phase 1: 基盤構築 ✅
- [x] 仮想環境構築
- [x] 依存関係設定
- [ ] プロジェクト構造作成
- [ ] 基本的なFastAPIアプリケーション
- [ ] WebSocket接続確立

### Phase 2: ゲームロジック実装
- [ ] ポーカーゲームエンジン
  - [ ] カードデッキ管理
  - [ ] ハンドランキング判定
  - [ ] ベッティングロジック
- [ ] シンプルAI実装
- [ ] ゲーム状態管理

### Phase 3: API実装
- [ ] ゲーム開始/終了API
- [ ] プレイヤーアクション処理
- [ ] ゲーム状態取得API
- [ ] WebSocketイベント処理

### Phase 4: フロントエンド実装
- [ ] Reactプロジェクト初期化
- [ ] ゲームUI作成
- [ ] カードコンポーネント
- [ ] ベッティングUI
- [ ] WebSocket通信

### Phase 5: 統合・テスト
- [ ] 結合テスト
- [ ] UI/UXテスト
- [ ] バグ修正・調整

## ゲーム仕様

### テキサスホールデム基本ルール
1. **プリフロップ**: 各プレイヤーに2枚のホールカード配布
2. **フロップ**: 3枚のコミュニティカード公開
3. **ターン**: 4枚目のコミュニティカード公開  
4. **リバー**: 5枚目のコミュニティカード公開
5. **ショーダウン**: 最強ハンドの判定

### プレイヤーアクション
- **フォールド**: ゲームを降りる
- **チェック**: ベットなしでパス
- **コール**: 相手のベットに合わせる
- **レイズ**: ベット額を上げる
- **オールイン**: 全チップをベット

### ハンドランキング（強い順）
1. ロイヤルストレートフラッシュ
2. ストレートフラッシュ
3. フォーカード
4. フルハウス
5. フラッシュ
6. ストレート
7. スリーカード
8. ツーペア
9. ワンペア
10. ハイカード

## データモデル

### ゲーム関連
```python
# Game State
class GameState(Enum):
    WAITING = "waiting"
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"
    FINISHED = "finished"

# Player Action
class PlayerAction(Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"
```

### WebSocketイベント
```typescript
// クライアント → サーバー
interface ClientEvents {
  join_game: { player_name: string };
  player_action: { action: PlayerAction; amount?: number };
  start_new_game: {};
}

// サーバー → クライアント  
interface ServerEvents {
  game_state: GameStateData;
  player_action_result: ActionResult;
  game_finished: GameResult;
  error: { message: string };
}
```

## 開発のポイント

### バックエンド開発
1. **ゲームロジックの分離**: ビジネスロジックをAPIから独立
2. **非同期処理**: FastAPIの非同期機能を活用
3. **エラーハンドリング**: 適切な例外処理とログ
4. **テスト駆動開発**: 複雑なゲームロジックは事前にテスト

### フロントエンド開発
1. **状態管理**: Reactの状態管理パターン
2. **リアルタイム更新**: WebSocketでの双方向通信
3. **レスポンシブデザイン**: モバイル対応
4. **アニメーション**: カード配布・アクションの視覚効果

## 次のステップ

1. **プロジェクト構造の作成**
2. **基本的なFastAPIアプリケーションのセットアップ**
3. **ポーカーゲームエンジンの実装開始**
4. **WebSocket接続の確立**

## 開発環境

### サーバー起動
```bash
cd server
# 仮想環境アクティベート
.\venv\Scripts\Activate.ps1
# 開発サーバー起動
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 今後のクライアント環境
```bash
cd client
npm install
npm run dev
```

## 参考資料

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/docs)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Texas Hold'em Rules](https://www.pokernews.com/poker-rules/texas-holdem.htm)