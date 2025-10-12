# Game Module

オンラインポーカーゲームのコア機能を管理するモジュールです。

## 構造

```
game/
├── README.md           # このファイル
├── __init__.py         # モジュール初期化
├── domain/            # ドメインモデル（ビジネスロジック）
│   ├── action.py      # プレイヤーアクション
│   ├── deck.py        # デッキとカード
│   ├── enum.py        # 列挙型定義
│   ├── game_state.py  # ゲーム状態管理
│   ├── player.py      # プレイヤー情報
│   ├── pot.py         # ポット管理
│   ├── seat.py        # 座席管理
│   └── table.py       # テーブル管理
└── services/          # ビジネスロジックサービス
    ├── betting_service.py    # ベッティング処理
    ├── game_service.py       # ゲーム全体の管理
    ├── hand_evaluator.py     # ハンド評価
    ├── hand_service.py       # ハンド関連処理
    ├── poker_engine.py       # ポーカーエンジン
    └── turn_manager.py       # ターン管理
```

## Domain層

ドメイン層には、ポーカーゲームの基本的なビジネスルールとエンティティが含まれています。

### 主要なクラス

- **Table**: ポーカーテーブルの状態と座席を管理
- **Seat**: 各座席の状態、プレイヤー、ベット額を管理
- **Player**: プレイヤーの基本情報
- **Deck**: カードデッキとシャッフル機能
- **GameState**: ゲーム全体の状態（フェーズ、コミュニティカードなど）
- **Pot**: ポットの管理（メインポット、サイドポット）
- **Action**: プレイヤーのアクション（フォールド、コール、レイズなど）

## Services層

サービス層には、ドメインオブジェクトを使用したビジネスロジックが含まれています。

### 主要なサービス

- **PokerEngine**: ゲーム全体のオーケストレーション
- **GameService**: ゲームセッションの管理
- **BettingService**: ベッティングラウンドの処理
- **HandEvaluator**: ハンドの強さを評価
- **HandService**: ハンド関連の処理
- **TurnManager**: プレイヤーのターン管理

## 使用方法

```python
from app.game.services.poker_engine import PokerEngine
from app.game.domain.table import Table

# テーブルを作成
table = Table(table_id="table_1", max_seats=6)

# ポーカーエンジンを初期化
engine = PokerEngine(table)

# ゲームを開始
engine.start_game()
```

## 設計原則

1. **ドメイン駆動設計**: ビジネスロジックをドメイン層に集約
2. **単一責任原則**: 各クラスは明確に定義された責任を持つ
3. **レイヤードアーキテクチャ**: サービス層がドメイン層を利用し、ドメイン層は外部依存を持たない
4. **テスタビリティ**: 各コンポーネントが独立してテスト可能

## 今後の拡張

- トーナメント機能
- 異なるポーカーバリアント（オマハ、スタッドなど）
- より詳細な統計機能
- AIプレイヤーの実装