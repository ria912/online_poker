# Online Poker Game - エージェント開発ガイド

## プロジェクト概要

### 最終目標
- **マルチプレイヤーオンラインポーカーゲーム**の実装
- リアルタイム対戦機能
- 複数のゲームルーム対応
- ランキング・統計機能

### 現在の目標
- **テキサスホールデムポーカーエンジン**の実装
- プレイヤー vs AI の対戦
- BBオプション対応の完全なポーカールール
- 基本的なゲームフロー完成

## 技術スタック

### バックエンド (`server/`)
- **FastAPI**: REST API & WebSocket通信
- **Python 3.11+**: メイン開発言語
- **treys**: ポーカーハンド評価ライブラリ
- **SQLAlchemy**: ORM（データベース操作）
- **SQLite**: 開発環境用DB
- **PostgreSQL**: 本番環境用DB（将来）
- **WebSocket**: リアルタイム通信

### フロントエンド (`client/`)
- **React**: UIフレームワーク（将来実装）
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
│   │   ├── game/             # ゲームロジック（メイン実装）
│   │   │   ├── domain/       # ドメインモデル
│   │   │   │   ├── action.py        # プレイヤーアクション
│   │   │   │   ├── deck.py          # デッキとカード
│   │   │   │   ├── enum.py          # 列挙型定義
│   │   │   │   ├── game_state.py    # ゲーム状態管理
│   │   │   │   ├── player.py        # プレイヤー情報
│   │   │   │   ├── seat.py          # 座席管理
│   │   │   │   └── table.py         # テーブル管理
│   │   │   └── services/     # ゲームサービス
│   │   │       ├── betting_service.py    # ベッティング処理
│   │   │       ├── dealer_service.py     # ディーラー処理
│   │   │       ├── game_service.py       # ゲーム全体管理
│   │   │       ├── hand_evaluator.py     # ハンド評価（treys）
│   │   │       ├── hand_service.py       # ハンド関連処理
│   │   │       ├── poker_engine.py       # ポーカーエンジン
│   │   │       └── turn_manager.py       # ターン管理
│   │   └── websocket/        # WebSocket処理
│   ├── tests/                # テストコード
│   │   └── test_bb_option.py # BBオプションテスト
│   ├── requirements.txt      # 依存関係
│   └── main.py               # アプリケーションエントリポイント
├── client/                    # フロントエンド（将来実装）
└── AGENT.md                  # このファイル
```

## 現在の実装状況

### Phase 1: 基盤構築 ✅
- [x] 仮想環境構築
- [x] 依存関係設定
- [x] プロジェクト構造作成
- [x] 基本的なFastAPIアプリケーション
- [x] WebSocket接続確立

### Phase 2: ゲームロジック実装 ✅
- [x] **ポーカーゲームエンジン完成**
  - [x] カードデッキ管理（treysライブラリ連携）
  - [x] ハンドランキング判定（treysベース）
  - [x] ベッティングロジック（BBオプション対応）
  - [x] ディーラー機能（カード配布、ポット管理）
  - [x] ターン管理（BBオプション、ヘッズアップ対応）
- [x] **ドメイン駆動設計実装**
- [x] **ゲーム状態管理完成**

### Phase 3: API実装 🚧
- [x] 基本的なAPI構造
- [ ] ゲーム開始/終了API
- [ ] プレイヤーアクション処理API
- [ ] ゲーム状態取得API
- [x] WebSocket基本実装

### Phase 4: フロントエンド実装 📋
- [ ] Reactプロジェクト初期化
- [ ] ゲームUI作成
- [ ] カードコンポーネント
- [ ] ベッティングUI
- [ ] WebSocket通信

### Phase 5: 統合・テスト 📋
- [x] 基本的なテスト（BBオプション）
- [ ] 結合テスト
- [ ] UI/UXテスト
- [ ] バグ修正・調整

## ゲーム仕様

### テキサスホールデム実装済み機能

#### 基本ルール ✅
1. **プリフロップ**: 各プレイヤーに2枚のホールカード配布
2. **フロップ**: 3枚のコミュニティカード公開
3. **ターン**: 4枚目のコミュニティカード公開  
4. **リバー**: 5枚目のコミュニティカード公開
5. **ショーダウン**: 最強ハンドの判定

#### プレイヤーアクション ✅
- **フォールド**: ゲームを降りる
- **チェック**: ベットなしでパス
- **コール**: 相手のベットに合わせる
- **レイズ**: ベット額を上げる
- **オールイン**: 全チップをベット

#### 特殊ルール ✅
- **BBオプション**: プリフロップでBBにチェック権利
- **ヘッズアップ**: 2人プレイ時のポジション調整
- **サイドポット**: オールイン時の複数ポット管理

#### ハンドランキング（treysライブラリ） ✅
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

## 実装済みアーキテクチャ

### Domain層（ドメインモデル）
```python
# 主要なドメインクラス
- GameState: ゲーム全体の状態管理
- Table: テーブルと座席の管理
- Seat: 各座席の状態（プレイヤー、ベット、カード）
- Player: プレイヤー情報
- Deck/Card: カードデッキ（treysライブラリ連携）
- Action: プレイヤーアクション（イミュータブル）
- Enums: ゲーム状態、アクション種別等の列挙型
```

### Services層（ビジネスロジック）
```python
# 専門サービス
- PokerEngine: ゲーム全体のオーケストレーション
- GameService: ゲームセッション管理
- DealerService: ディーラー機能（カード配布、ポット回収）
- BettingService: ベッティング処理
- TurnManager: ターン管理（BBオプション対応）
- HandEvaluator: ハンド評価（treysライブラリ）
- HandService: ショーダウン処理
```

## 使用方法

### 基本的なゲーム作成と実行
```python
from app.game.services.game_service import GameService
from app.game.domain.player import Player
from app.game.domain.enum import ActionType

# ゲームサービス初期化
game_service = GameService()

# ゲーム作成
game = await game_service.create_game("game_1", big_blind=100)

# プレイヤー参加
player1 = Player("p1", "Alice")
player2 = Player("p2", "Bob")
await game_service.join_game("game_1", player1)
await game_service.join_game("game_1", player2)

# ゲーム開始
await game_service.start_game("game_1")

# プレイヤーアクション
success = await game_service.process_player_action(
    "game_1", "p1", ActionType.CALL, amount=100
)

# ゲーム状態取得
game_state = game_service.get_game_state("game_1")
```

### WebSocket通信例
```python
# server/app/websocket/router.py
# ゲーム用WebSocketエンドポイント: /ws/game/{game_id}

# クライアント → サーバー
{
  "type": "player_action",
  "action": "CALL",
  "amount": 100
}

# サーバー → クライアント
{
  "type": "game_state_update",
  "game_state": {...},
  "valid_actions": ["FOLD", "CALL", "RAISE"]
}
```

### テスト実行
```bash
cd server
python tests/test_bb_option.py  # BBオプション機能テスト
```

## API仕様（実装予定）

### REST API
```python
# ゲーム管理
GET    /api/v1/games          # ゲーム一覧
POST   /api/v1/games          # ゲーム作成
GET    /api/v1/games/{id}     # ゲーム状態取得
POST   /api/v1/games/{id}/start  # ゲーム開始
POST   /api/v1/games/{id}/action # プレイヤーアクション
```

### WebSocket Events
```typescript
// クライアント → サーバー
interface ClientEvents {
  join_game: { player_name: string };
  player_action: { action: ActionType; amount?: number };
  start_new_game: {};
  chat_message: { message: string };
}

// サーバー → クライアント  
interface ServerEvents {
  game_state_update: GameStateData;
  player_action_result: ActionResult;
  game_finished: GameResult;
  player_joined: PlayerInfo;
  player_disconnected: PlayerInfo;
  error: { message: string };
}
```

## 設計原則

### 実装済み設計パターン
1. **ドメイン駆動設計**: ビジネスロジックをドメイン層に集約
2. **レイヤードアーキテクチャ**: Services → Domain の依存関係
3. **単一責任原則**: 各サービスクラスは明確な責務を持つ
4. **イミュータブルデータ**: Actionクラスはdataclass(frozen=True)
5. **依存性注入**: サービス間の疎結合

### コード品質
- **型安全性**: Python型ヒント完全対応
- **テスタビリティ**: 各コンポーネントが独立してテスト可能
- **拡張性**: 新しいポーカーバリアント追加可能な設計

## 今後の開発計画

### 短期（1-2週間）
1. **API層の完成**: REST APIエンドポイント実装
2. **WebSocket統合**: ゲームロジックとWebSocket連携
3. **AIプレイヤー**: 基本的なAI実装
4. **フロントエンド開始**: React環境構築

### 中期（1-2ヶ月）
1. **UI実装**: ポーカーテーブルUI
2. **リアルタイム機能**: WebSocketでのゲーム状態同期
3. **統計機能**: プレイヤー統計・履歴
4. **トーナメント機能**: 基本的なトーナメント

### 長期（3-6ヶ月）
1. **マルチプレイヤー**: 複数テーブル対応
2. **ランキングシステム**: レーティング実装
3. **高度なAI**: より賢いAIプレイヤー
4. **モバイル対応**: レスポンシブデザイン

## 開発環境

### サーバー起動
```bash
cd server
# 仮想環境アクティベート
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Mac/Linux

# 依存関係インストール
pip install -r requirements.txt

# 開発サーバー起動
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 依存関係
```txt
# 主要ライブラリ
fastapi==0.104.1          # Web framework
uvicorn==0.24.0           # ASGI server
treys==0.1.8              # Poker hand evaluation
pydantic==2.5.0           # Data validation
python-socketio==5.10.0   # WebSocket support
pytest==7.4.3            # Testing framework
```

### 開発ツール（オプション）
```bash
# コード品質ツール
pip install -r requirements-dev-optional.txt

# フォーマット
black server/                    # コードフォーマット
isort server/                    # インポート整理

# 型チェック
mypy server/app/                 # 型検証

# テストカバレッジ
pytest --cov=app tests/          # カバレッジ付きテスト
```

## トラブルシューティング

### 一般的な問題
1. **インポートエラー**: Pythonパスの確認
2. **treysライブラリ**: `pip install treys`で解決
3. **WebSocket接続**: CORS設定を確認
4. **テスト失敗**: 依存関係の不整合

### デバッグ方法
```python
# ゲーム状態の確認
game_state = game_service.get_game_state("game_1")
print(f"現在のラウンド: {game_state.current_round}")
print(f"現在のベット: {game_state.current_bet}")

# 座席状態の確認
for seat in game_state.table.seats:
    if seat.is_occupied:
        print(f"座席{seat.index}: {seat.player.name} - {seat.current_stack}チップ")
```

## 参考資料

### 技術資料
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [treys Library](https://github.com/ihendley/treys)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

### ポーカールール
- [Texas Hold'em Rules](https://www.pokernews.com/poker-rules/texas-holdem.htm)
- [Big Blind Option](https://www.pokernews.com/strategy/big-blind-option-preflop-28044.htm)
- [Side Pot Rules](https://www.pokernews.com/poker-rules/side-pots.htm)

## プロジェクト進捗

### 完了済み ✅
- [x] 完全なポーカーエンジン実装
- [x] BBオプション対応
- [x] サイドポット計算
- [x] treysライブラリ統合
- [x] ドメイン駆動設計
- [x] 基本テスト実装

### 進行中 🚧
- [ ] API層の完成
- [ ] WebSocket統合

### 計画中 📋
- [ ] フロントエンド実装
- [ ] AIプレイヤー
- [ ] トーナメント機能

このプロジェクトは堅実なアーキテクチャの上に構築されており、将来の拡張性を考慮した設計となっています。