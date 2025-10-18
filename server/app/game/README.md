# Game Module（統合ガイド）

テキサスホールデムのゲームロジック全体を統括するモジュールです。ドメイン層（ルール）とサービス層（進行）を組み合わせ、完全なポーカーゲームを実現します。

---

## モジュール構成

```
game/
├── README.md              # このファイル（統合ガイド）
├── __init__.py
├── domain/                # ビジネスルールの中核
│   ├── README.md         # ドメイン層の詳細ガイド
│   ├── action.py         # プレイヤーアクション（値オブジェクト）
│   ├── deck.py           # カードとデッキ
│   ├── enum.py           # 列挙型（ラウンド/ステータス/アクション/ポジション）
│   ├── game_state.py     # ゲーム状態の集約ルート
│   ├── player.py         # プレイヤーエンティティ
│   ├── seat.py           # 座席の状態管理
│   └── table.py          # テーブル・ポット・共有状態
└── services/             # ゲーム進行のオーケストレーション
    ├── README.md         # サービス層の詳細ガイド
    ├── action_service.py # アクション適用と検証
    ├── dealer_service.py # ディーラー責務（配布/ブラインド/ポット）
    ├── game_service.py   # ゲームセッション管理
    ├── hand_evaluator.py # ハンド評価（treys）
    ├── hand_service.py   # ショーダウン処理
    ├── poker_engine.py   # コア進行エンジン
    └── turn_manager.py   # ターン管理とアクター選定
```

---

## アーキテクチャの全体像

### レイヤー構造

```
┌─────────────────────────────────────────┐
│  API / WebSocket Layer                  │  ← 外部インターフェース
│  (router.py)                            │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  Services Layer                         │  ← ゲーム進行の編成
│  (game_service, poker_engine, etc.)    │     ・いつ何をするか
└─────────────────────────────────────────┘     ・副作用の集約
              ↓
┌─────────────────────────────────────────┐
│  Domain Layer                           │  ← ビジネスルールの真実
│  (game_state, table, seat, player)     │     ・何が正しい状態か
└─────────────────────────────────────────┘     ・不変条件の保持
```

### 設計原則

- **関心の分離**: ドメインは「ルール」、サービスは「進行」、APIは「通信」
- **依存の方向**: サービス → ドメイン（逆方向の依存は禁止）
- **集約の明確化**: `GameState` が唯一の真実の情報源（Single Source of Truth）
- **純粋性の追求**: ドメインは副作用なし、サービスで副作用を局所化

---

## 主要な概念と責務

### ドメイン層の責務

- **状態の表現**: テーブル、座席、プレイヤー、カード、ベット額など
- **不変条件の保持**: スタック非負、ホールカード2枚、デッキ重複なし
- **状態遷移ルール**: 新ハンド/新ラウンド時のリセット、座席ステータス管理
- **クエリ提供**: アクティブ座席、ハンド参加者、ラウンド終了判定

**詳細**: [`domain/README.md`](./domain/README.md)

### サービス層の責務

- **進行のオーケストレーション**: ハンド開始、アクション処理、ラウンド遷移
- **副作用の実行**: シャッフル、配布、ベット回収、通知トリガー
- **入力検証**: 有効なアクションか、現在のターンか
- **ビジネスフロー**: ディーラーボタン回転、ブラインド徴収、ショーダウン

**詳細**: [`services/README.md`](./services/README.md)

---

## 典型的なゲームフロー

### 1. ゲーム作成と参加

```python
# GameService を使用
game_service = GameService()
game = await game_service.create_game("table_1", big_blind=100)
await game_service.join_game("table_1", player1)
await game_service.join_game("table_1", player2)
```

### 2. ハンド開始

```python
# PokerEngine が DealerService/TurnManager を統合
await game_service.start_game("table_1")
# → ボタン回転 → ブラインド → ホールカード配布 → 最初のアクター設定
```

### 3. ベッティングラウンド

```python
# プレイヤーがアクションを実行
valid_actions = game_service.get_valid_actions("table_1", "player_1")
# → [FOLD, CALL, RAISE]

await game_service.process_player_action(
    "table_1", "player_1", ActionType.RAISE, amount=300
)
# → ActionService でスタック更新 → TurnManager で次のアクター
```

### 4. ラウンド遷移とショーダウン

```python
# ベッティング完了後、自動でフロップ/ターン/リバー配布
# 最終ラウンド終了後、ショーダウンへ
# → HandService でハンド評価 → 勝者確定 → ポット分配
```

---

## 重要な設計判断

### スタックの所在

- **以前**: `Player.stack` に保持（複数テーブル対応が困難）
- **現在**: `Seat.stack` に保持（各テーブルで独立管理）
- **理由**: マルチテーブル/トーナメント拡張、座席単位の整合性

### スタック操作の一元化

- **方針**: `Seat.pay(amount)` / `Seat.refund(amount)` で一元管理
- **効果**: `bet_in_round`/`bet_in_hand` との整合性を自動保証
- **場所**: サービス層で呼び出し（CALL/BET/RAISE/ブラインド徴収）

### ベッティングロジック

- **current_bet**: ラウンド中の最大総ベット額（座席視点の総額）
- **bet_in_round**: 各座席の現在ラウンドでのベット累計
- **last_raise_delta**: 最後のレイズ幅（最小レイズ計算に使用）

### ラウンド終了判定

- **実装**: `TurnManager.is_betting_round_complete()`
- **条件**: アクティブ座席 ≤1 or 全員が acted かつ bet_in_round == current_bet
- **統一**: サービス層で一元化（`Table.is_round_over` は補助的）

---

## 拡張ポイント

### すぐに実装可能

- **ポジション付与**: `PositionService.assign_positions()` をハンドセットアップに統合
- **ログ/監査**: アクション履歴を構造化ログに出力
- **テスト**: シナリオベーステスト（2-3人、プリフロップ→ショーダウン）

### 中期的な拡張

- **ルール設定**: ブラインド構造/アンティ/ミニマムレイズを設定オブジェクト化
- **AI プレイヤー**: `Player.is_ai` を活用した自動アクション
- **マルチテーブル**: 同一プレイヤーが複数 `GameState` に参加
- **リバイ/アドオン**: `Seat.stack` への追加購入処理

### 長期的な拡張

- **トーナメント**: ブラインドレベル管理、席替え、チップカウント
- **他バリアント**: オマハ/スタッド（ドメインモデルの部分拡張）
- **リプレイ機能**: `GameState.history` を永続化して再生
- **統計/解析**: プレイヤー統計、ハンドレンジ分析

---

## 学習の進め方

### 初学者向け

1. **列挙型の理解**: `domain/enum.py` で用語（Round/SeatStatus/ActionType）を確認
2. **状態の理解**: `domain/seat.py` → `domain/table.py` → `domain/game_state.py` の順で読む
3. **進行の理解**: `services/poker_engine.py` の `start_new_hand()` と `process_action()` を追う
4. **小さな例**: 2人プレイのシナリオを紙に書き、コードと対応づける

### 中級者向け

1. **ラウンド遷移**: `TurnManager` と `DealerService` の連携を把握
2. **アクション検証**: `ActionService.is_valid_action()` のルールを整理
3. **ポット計算**: `DealerService.collect_bets_to_pots()` のサイドポット処理
4. **ショーダウン**: `HandService` と `HandEvaluator` の役割分担

### 上級者向け

1. **不変条件の検証**: ドメインのプロパティベーステスト
2. **並行性の考慮**: 複数テーブル同時進行時の状態管理
3. **パフォーマンス**: ハンド評価のキャッシュ、状態更新の最適化
4. **拡張実装**: トーナメント/オマハへの拡張設計

---

## トラブルシューティング

### よくある問題

- **アクションが拒否される**: `TurnManager.get_valid_actions_for_player()` で提示されるアクションを確認
- **ラウンドが進まない**: `is_betting_round_complete()` の条件（全員 acted、ベット一致）を検証
- **スタック不整合**: `Seat.pay()` を使わず直接 `seat.stack` を操作していないか確認
- **ポット計算ミス**: サイドポット対象者（`eligible_seats`）とオールイン順序を確認

### デバッグのヒント

- `GameState.history` でアクション履歴を確認
- `game.table.active_seats()` で現在のアクティブ座席を確認
- `seat.bet_in_round` と `game.current_bet` の差分でコール額を計算
- `game.current_seat_index` と各座席の `acted` フラグで進行状況を把握

---

## 参考資料

- **ドメイン層**: [`domain/README.md`](./domain/README.md)
- **サービス層**: [`services/README.md`](./services/README.md)
- **テキサスホールデムルール**: [公式ポーカールール](https://www.pokernews.com/poker-rules/texas-holdem.htm)
- **treys ライブラリ**: [GitHub - worldveil/treys](https://github.com/worldveil/treys)

---

## コントリビューション指針

- **ドメイン変更**: 不変条件に影響する場合、必ず単体テストを追加
- **サービス追加**: 既存サービスとの責務重複を確認
- **API 変更**: 破壊的変更は避け、新メソッド追加で拡張
- **命名規則**: Python PEP8 に準拠、メソッド名は動詞から開始

このモジュールは学習と実践の両方を意図して設計されています。各層の README も合わせてご覧ください。
