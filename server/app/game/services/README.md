# Services 層（学習用ガイド）

このフォルダは、ドメインを組み合わせて「ゲーム進行」を実現するアプリケーションロジックをまとめます。乱数（配布）、アクターの選定、入力検証、状態遷移の編成、通知トリガーなどを担当します。外部I/Oの詳細（DB/ネットワーク）はここでは扱いません。

---

## 設計思想（Principles）

- オーケストレーション: いつ何をするかの順序を決め、ドメインの操作を組み立てる。
- ドメインの尊重: ルールの真実は domain/ にある。サービスはルールを破らないよう補助・整合化する。
- 副作用の集約: シャッフルや配布、アクション適用、フロー制御はサービス側で完結させる。
- テスタビリティ: できる限り純粋な計算で書き、依存は注入可能にする（将来）。

---

## ファイル一覧と役割

- `game_service.py`
  - ゲームセッションのライフサイクル管理（作成/参加/開始/アクション委譲）。外部インターフェースの窓口。
- `poker_engine.py`
  - コア進行のオーケストレータ。新ハンド開始、アクション処理、ラウンド遷移、ショーダウン進行を束ねる。
- `dealer_service.py`
  - ディーラー責務。ボタン回転、ブラインド設定、ホール/ボード配布、ベット回収（ポット計算）。
- `turn_manager.py`
  - アクター選定とラウンド完了判定。最初のアクター設定、次アクター算出、有効アクションの提示を担当。
- `action_service.py`
  - ベッティングアクションの適用と詳細検証。`FOLD/CHECK/CALL/BET/RAISE` の状態変更を一元化。
- `hand_service.py`
  - ショーダウン用のハンド評価と勝者確定（実評価は `hand_evaluator.py`）。
- `hand_evaluator.py`
  - 最小APIのハンド評価（treys Evaluator）。`evaluate_hand()` と `get_hand_name()` を提供。

---

## 典型フロー

1. `GameService.start_game()`
2. `PokerEngine.start_new_hand()`
   - `Table.reset_for_new_hand()`（ドメイン）
   - `DealerService.rotate_dealer_button()` → `set_blind_positions()`
   - `DealerService.deal_hole_cards()` → `collect_blinds()`
   - `TurnManager.set_first_actor_for_round()`
3. `PokerEngine.process_action(PlayerAction)`
   - `TurnManager.get_valid_actions_for_player()`
   - `ActionService.execute_action()` → 状態更新
   - `TurnManager.advance_to_next_actor()`／`is_betting_round_complete()`
   - ラウンド終了なら `DealerService.collect_bets_to_pots()` → 次ラウンド配布
4. `PokerEngine._proceed_to_showdown()`
   - `HandService.evaluate_showdown()` → `GameState.winners` を確定

---

## 責務境界のルール

- ドメインは状態と制約、サービスは進行と副作用。
- スタック・ベット加算は一貫した場所で行う（将来は `Seat.pay()` 等へ集約を検討）。
- UI都合の情報（`valid_actions` 等）は原則サービスで計算し、ドメインに持ち込まない。

---

## 公開APIの目安

- `GameService`
  - `create_game(game_id, big_blind=100)` → `GameState`
  - `join_game(game_id, player)` → `bool`
  - `start_game(game_id)` → `bool`
  - `process_player_action(game_id, player_id, action_type, amount=None)` → `bool`
  - `get_game_state(game_id)` → `GameState | None`
  - `get_valid_actions(game_id, player_id)` → `List[ActionType]`

- `PokerEngine`
  - `start_new_hand(game)` → `bool`
  - `process_action(game, PlayerAction)` → `bool`
  - `get_valid_actions(game, player_id)` → `List[ActionType]`

---

## 拡張指針

- ルール差し替え: ミニマムレイズ/アンティ/ストラクチャは設定オブジェクトへ抽象化。
- ポジション: `PositionService` などを導入し、6-max/フルリング/ヘッズアップの命名を統一化（必要に応じて）。
- サイドポット: 現状の回収ロジックの単体テストを増やし、不正ケース（途中オールイン、引き分け）を網羅。
- バリデーション: `ActionService.is_valid_action()` を強化（ミニマムレイズ、リオープン、オプションチェック等）。

---

## テストの観点

- ユニット: `TurnManager` のアクター選定、`DealerService` の配布・ポット回収、`ActionService` の各アクション適用。
- シナリオ: プリフロップからショーダウンまでの一連進行（2-3人）。
- 退行防止: 公開APIのインタフェース・ドメイン属性を固定し、破壊的変更を検知。
