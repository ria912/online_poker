# Domain 層（学習用ガイド）

このフォルダは、テキサスホールデムにおける「ビジネスルールの中核（ルールの真実の在処）」を表現します。外部I/O（DB/ネットワーク/ログ）やUI都合の値は持たず、ポーカーの状態と不変条件を厳密に扱います。

---

## 設計思想（Principles）

- **単一責任**: 各クラスはテーブル/座席/プレイヤー/山札/状態などの1つの概念に責務を限定します。
- **不変条件の保持**: スタックが負の値にならない、ホールカードは2枚など、ゲームの基本制約をクラス内部で守ります。
- **集約の一貫性**: `GameState` を集約ルートとし、現在のラウンド・ベット状況など「ハンドの真実」を一元管理します。
- **副作用の隔離**: ランダム性（シャッフル）やメッセージ送出はサービス層。ドメインは純粋な状態遷移と検証に集中します。
- **表現の明確さ**: `enum.py` の列挙で状態/アクション/ポジションを明示し、マジックナンバーを排除します。
- **支払い処理の一元化**: `Seat.pay()` メソッドでスタック操作を統一し、整合性を保証します。

---

## ファイル一覧と役割

### `action.py`
値オブジェクト `PlayerAction` を定義。プレイヤーID、アクション種別、金額（任意）を持つ不変データ。

### `deck.py`
`Card` と `Deck` を定義。シャッフルとドローのみを提供。`Card.to_treys_int()` で treys 評価器との橋渡しを行います。

### `enum.py`
列挙型を定義：
- `Round`: PREFLOP/FLOP/TURN/RIVER/SHOWDOWN
- `SeatStatus`: EMPTY/ACTIVE/FOLDED/ALL_IN/SITTING_OUT
- `ActionType`: FOLD/CHECK/CALL/BET/RAISE/ALL_IN
- `Position`: SB/BB/BTN/UTG/MP/CO
- `GameStatus`: WAITING/IN_PROGRESS/HAND_COMPLETE

### `game_state.py`
ハンド全体の状態を表現する集約ルート。
- 現在のラウンド、ボタン/ブラインド位置、現在ベット額
- 最小レイズ幅（`last_raise_delta`）、最後のアグレッシブアクター
- アクション履歴、参加プレイヤー、勝者リスト、テーブル参照を保持
- 新ハンド/新ラウンド開始時の初期化メソッドで状態の整合性を保ちます

### `player.py`
プレイヤーのID・表示名・AIフラグなど最小情報を保持するエンティティ。

### `seat.py`
各座席の状態を管理：
- 着席者、スタック、ホールカード、ポジション
- ラウンド内/ハンド内のベット（`bet_in_round`, `bet_in_hand`）
- 行動フラグ（`acted`, `last_action`）、ステータス（`status`）
- **重要**: `pay(amount)` メソッドでスタック操作を一元化
  - 実際の支払額を返却（スタック不足時は利用可能額のみ）
  - `stack`, `bet_in_round`, `bet_in_hand` を同時更新し整合性を保証
- `refund(amount)`: 払い戻し処理
- `sit_down(player, stack)`: プレイヤーを着席
- `stand_up()`: プレイヤーを退席
- `clear_for_new_hand()`, `reset_for_new_round()`: 状態リセット

### `table.py`
テーブル上の共有状態を管理：
- コミュニティカード、ポット群、座席配列、デッキ
- 新ハンド/新ラウンド用のリセットメソッド
- 補助クエリ: `in_hand_seats()`, `active_seats()`, `empty_seats()`, `occupied_seats()`

### `__init__.py`
ドメイン公開のエントリーポイント。

---

## 不変条件・整合性ルール

- 1プレイヤーのホールカードは常に2枚
- デッキは重複カードを含まない
- `SeatStatus.EMPTY` は `player is None` を意味
- `ACTIVE/FOLDED/ALL_IN` は `player is not None` を前提
- `bet_in_round` はラウンド切替時に 0 にリセット
- `GameState.current_bet` はラウンド中の最大投入額（総額）
- **スタック操作は必ず `Seat.pay()` を経由** し、負の値にならない

---

## 典型的な状態遷移

1. **新ハンド開始**: `Table.reset_for_new_hand()` → 各 `Seat.clear_for_new_hand()`
2. **ディーラーボタン回転・ブラインド設定**（サービス側）→ `GameState.dealer_seat_index` 等が更新
3. **ホールカード配布**（サービス側）→ `Seat.receive_cards()`
4. **ベットラウンド**: `Seat.pay()` でベット額更新、`current_bet` を同期
5. **ラウンド終了**: `Table.reset_for_new_round()` → 各 `Seat.reset_for_new_round()`
6. **ショーダウン**: ハンド評価 → ポット分配 → `GameState.status = HAND_COMPLETE`

---

## サービス層との境界

- **ドメイン**: 「何が正しい状態か」を表現し、操作の原子性や制約を担保
- **サービス**: 「いつ・どの順序で行うか」を司り、入出力（プレイヤー操作、配布、通知）をまとめる
- **スタック操作**: `Seat.pay()` を使用してドメインで整合性を保証
- **配列操作**: `Deck.shuffle()`, `Deck.draw()` などの副作用はサービス側から呼び出し

---

## リアルタイムシングルプレイ向け拡張指針

### 1. AI対戦相手の強化
```python
# player.py に追加
class Player:
    ai_difficulty: str = "medium"  # easy/medium/hard
    ai_strategy: Optional[str] = None  # tight/loose/aggressive
```

### 2. ゲーム速度制御
```python
# game_state.py に追加
class GameState:
    animation_speed: float = 1.0  # 0.5-2.0
    auto_fold_timeout: int = 30  # 秒
    fast_forward_enabled: bool = False
```

### 3. プレイヤー統計トラッキング
```python
# seat.py に追加
class SeatStatistics:
    hands_played: int = 0
    vpip: float = 0.0  # Voluntarily Put In Pot
    pfr: float = 0.0   # Pre-Flop Raise
    aggression_factor: float = 0.0
```

### 4. リプレイ機能
```python
# game_state.py に追加
class GameState:
    hand_history: List[Dict] = []  # 全アクション履歴
    replay_enabled: bool = True
```

### 5. チュートリアル・ヒント機能
```python
# 推奨アクションの計算
def suggest_action(game: GameState, seat: Seat) -> Dict:
    return {
        "action": ActionType.CALL,
        "reason": "pot_odds_favorable",
        "confidence": 0.75
    }
```

---

## 拡張指針（一般）

- **ルール差し替え**: ブラインド額/最小レイズ幅/テーブルサイズは設定オブジェクト化して `GameState` に注入
- **役判定の強化**: 現在は treys を使用。別評価器へ差し替えしやすいよう `Card.to_treys_int()` は維持
- **ショートハンド/ヘッズアップ特則**: `Position` 付与ロジックはサービス側に実装
- **マルチテーブル**: `GameState` を複数管理し、各テーブルで独立した進行を実現

---

## 学習の観点での読み方

1. **enum.py**: 用語とステート定義を把握
2. **seat.py**: 個別座席の状態管理と `pay()` メソッド
3. **table.py**: 座席の集合とコミュニティ情報
4. **game_state.py**: 全体の集約ルートとハンド進行
5. **deck.py / action.py**: 小さな値オブジェクト

この順で読むと、サービス層のコード（進行/配布/評価）を理解する際の前提がクリアになります。