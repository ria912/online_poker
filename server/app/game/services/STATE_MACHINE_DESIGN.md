# PokerEngine ステートマシン設計

## 概要

`PokerEngine.process_action` は、プレイヤーアクションを受け取り、ゲーム状態を適切に遷移させるステートマシンとして機能します。この設計により、複雑なゲームフローを明確かつ拡張性の高い形で管理できます。

---

## ステートマシンの動作フロー

```python
async def process_action(self, game: GameState, action: PlayerAction) -> bool:
    # (1) アクション検証
    if not self._is_valid_action(game, action):
        return False
    
    # (2) アクション実行
    success = await self.action_service.execute_action(game, action)
    if not success:
        return False
    
    game.history.append(action)
    
    # (3) 次のアクターに進む
    round_continues = self.turn_manager.advance_to_next_actor(game)
    
    if round_continues:
        # ラウンド継続: 次のプレイヤーのアクション待ち
        return True
    
    # ここから先はベッティングラウンド終了時の処理
    
    # (4) ベットをポットに回収
    self.dealer_service.collect_bets_to_pots(game)

    # (5) フォールド勝ちチェック
    if len(game.table.in_hand_seats()) <= 1:
        return self._proceed_to_fold_win(game)

    # (6) リバーのベッティング終了チェック
    if game.current_round == Round.RIVER:
        self._proceed_to_showdown(game)
        return True
        
    # (7) 次のストリートへ進む
    self._advance_to_next_street(game)
    
    # (8) 自動進行 (Run it out) チェック
    return self._check_and_run_it_out(game)
```

---

## 状態遷移図

```
[アクション実行]
    ↓
[次のアクター判定]
    ↓
┌─── ラウンド継続? ─── YES → [次のプレイヤー待ち] (終了)
│
NO (ラウンド終了)
    ↓
[ベット回収]
    ↓
┌─── in_hand <= 1? ─── YES → [フォールド勝ち] (終了)
│
NO
    ↓
┌─── RIVER終了? ─── YES → [ショーダウン] (終了)
│
NO
    ↓
[次のストリートへ]
    ↓
┌─── active <= 1 かつ in_hand > 1? ─── YES → [自動進行: リバーまで] → [ショーダウン] (終了)
│
NO
    ↓
[次のプレイヤー待ち] (終了)
```

---

## 主要メソッドの責務

### `_advance_to_next_street(game)`
**責務**: 次のストリートに進み、ターンをリセットする

- コミュニティカードを配布（`DealerService.deal_community_cards`）
- ターン状態をリセット（`TurnManager.reset_for_new_round`）
- 最初のアクターを設定（`TurnManager.set_first_actor_for_round`）

**注意**: ベット回収は `process_action` 側で実行済み

### `_check_and_run_it_out(game)`
**責務**: 自動進行(Run it out)の判定と実行

**条件**:
- `active_seats_count <= 1` (アクション可能なプレイヤーが1人以下)
- `in_hand_seats_count > 1` (ハンド参加者が複数)

**動作**:
1. 条件を満たす場合、リバーまで一気にカードを配布
2. ショーダウンに進む

**典型的なシナリオ**:
- フロップで全員オールイン → ターン、リバーを自動配布 → ショーダウン
- 1人がオールイン、他全員フォールド → フォールド勝ち処理（このメソッドは呼ばれない）

### `_proceed_to_fold_win(game)`
**責務**: フォールド勝ちの処理

**動作**:
1. ハンド評価を実行（`HandService.evaluate_hands_for_showdown`）
   - 1人勝ちでも正しく評価される
2. ポット分配を実行（`DealerService.distribute_pots`）
3. ゲーム終了状態に設定（`GameStatus.HAND_COMPLETE`）

### `_proceed_to_showdown(game)`
**責務**: ショーダウン処理

**動作**:
1. ラウンドを `Round.SHOWDOWN` に設定
2. 全プレイヤーのカードを公開（`seat.show_hand = True`）
3. ハンド評価を実行（`HandService.evaluate_hands_for_showdown`）
4. ポット分配を実行（`DealerService.distribute_pots`）
5. ゲーム終了状態に設定（`GameStatus.HAND_COMPLETE`）

---

## 設計の利点

### 1. 明確な状態遷移
各状態遷移が `process_action` 内で一元管理されており、ゲームフローが追いやすい。

### 2. 拡張性の高さ
新しい状態遷移ルールを追加する場合、`process_action` に条件分岐を追加するだけ。

### 3. 責務の分離
- `PokerEngine`: いつ何をするかを決定（オーケストレーション）
- 専門サービス: 実務を実行（カード配布、ベット処理など）

### 4. テスタビリティ
各状態遷移を個別にテスト可能。モックを使って特定の状態をシミュレートしやすい。

---

## 自動進行(Run it out)の実装詳細

### 背景
ポーカーでは、全プレイヤーがオールインまたはフォールドした状態では、それ以降のアクションが発生しません。しかし、複数人がハンドに残っている場合、ショーダウンのために残りのコミュニティカードを配布する必要があります。

### 判定条件
```python
active_seats_count = len(game.table.active_seats())
in_hand_seats_count = len(game.table.in_hand_seats())

if active_seats_count <= 1 and in_hand_seats_count > 1:
    # 自動進行が必要
```

**解説**:
- `active_seats`: アクション可能な座席（フォールドしておらず、スタックが残っている）
- `in_hand_seats`: ハンドに参加している座席（フォールドしていない）

### 実装
```python
def _check_and_run_it_out(self, game: GameState) -> bool:
    active_seats_count = len(game.table.active_seats())
    in_hand_seats_count = len(game.table.in_hand_seats())

    if active_seats_count <= 1 and in_hand_seats_count > 1:
        # リバーまで一気にカードを配る
        while game.current_round != Round.RIVER:
            self.dealer_service.deal_community_cards(game)
        
        # ショーダウンへ
        self._proceed_to_showdown(game)
    
    return True
```

**重要な点**:
- `_advance_to_next_street` ではなく `deal_community_cards` を直接呼ぶ
- ターンリセットやベット回収は不要（全員オールインまたはフォールド済み）

### シナリオ例

#### シナリオ1: フロップで全員オールイン
```
[PREFLOP] PlayerA: CALL, PlayerB: ALL-IN, PlayerC: ALL-IN
↓ 全員のアクション終了
↓ _advance_to_next_street() でフロップ配布
↓ _check_and_run_it_out() が呼ばれる
↓ active_seats = 0, in_hand_seats = 3 → 条件満たす
↓ ターンとリバーを自動配布
↓ ショーダウン
```

#### シナリオ2: フロップで1人がベット、他全員フォールド
```
[FLOP] PlayerA: BET, PlayerB: FOLD, PlayerC: FOLD
↓ in_hand_seats = 1 → _proceed_to_fold_win() が呼ばれる
↓ _check_and_run_it_out() は呼ばれない
```

#### シナリオ3: フロップで1人がベット、1人がコール
```
[FLOP] PlayerA: BET, PlayerB: CALL, PlayerC: FOLD
↓ active_seats = 2, in_hand_seats = 2 → 条件満たさない
↓ 通常通りターンに進む
```

---

## 今後の拡張可能性

### 1. アニメーション制御
自動進行時にカード配布のアニメーションを段階的に表示する場合、`_check_and_run_it_out` にタイミング制御を追加できます。

```python
async def _check_and_run_it_out(self, game: GameState) -> bool:
    if active_seats_count <= 1 and in_hand_seats_count > 1:
        while game.current_round != Round.RIVER:
            self.dealer_service.deal_community_cards(game)
            # アニメーション待機
            await self._emit_community_cards_event(game)
            await asyncio.sleep(0.5)  # カード配布間隔
        
        self._proceed_to_showdown(game)
    
    return True
```

### 2. ログとリプレイ
自動進行時に特別なログを記録することで、リプレイ機能で「Run it out」を再現できます。

```python
if active_seats_count <= 1 and in_hand_seats_count > 1:
    game.history.append(GameEvent(type="RUN_IT_OUT", round=game.current_round))
```

### 3. トーナメント対応
トーナメントでは、複数テーブルで同時に自動進行が発生する可能性があります。現在の設計は非同期対応なので、並行処理が容易です。

---

## テスト戦略

### ユニットテスト
- `_check_and_run_it_out` が条件を正しく判定するか
- リバーまで正しくカードが配布されるか
- ショーダウンが正しく実行されるか

### 統合テスト
- フロップで全員オールイン → リバーまで自動進行
- フロップで1人がベット、1人がオールイン、1人がフォールド → ターンに通常進行
- ターンで全員オールイン → リバーのみ自動配布

### シナリオテスト
```python
async def test_run_it_out_on_flop():
    # 3人でゲーム開始
    game = create_test_game(players=3)
    poker_engine.start_new_hand(game)
    
    # プリフロップ: 全員がコール
    await poker_engine.process_action(game, PlayerAction(player_id="p1", action_type=ActionType.CALL))
    await poker_engine.process_action(game, PlayerAction(player_id="p2", action_type=ActionType.CALL))
    await poker_engine.process_action(game, PlayerAction(player_id="p3", action_type=ActionType.CHECK))
    
    # フロップ: 全員がオールイン
    await poker_engine.process_action(game, PlayerAction(player_id="p1", action_type=ActionType.BET, amount=1000))
    await poker_engine.process_action(game, PlayerAction(player_id="p2", action_type=ActionType.RAISE, amount=2000))
    await poker_engine.process_action(game, PlayerAction(player_id="p3", action_type=ActionType.CALL, amount=2000))
    await poker_engine.process_action(game, PlayerAction(player_id="p1", action_type=ActionType.CALL, amount=1000))  # All-in
    
    # 検証: ゲームがSHOWDOWNに到達し、全てのコミュニティカードが配布されている
    assert game.current_round == Round.SHOWDOWN
    assert len(game.table.community_cards) == 5
    assert game.status == GameStatus.HAND_COMPLETE
```

---

## まとめ

`PokerEngine` のステートマシン設計により、以下を実現しました:

1. **明確な状態遷移**: ゲームフローが `process_action` で一元管理
2. **責務の分離**: オーケストレーションと実務の明確な分離
3. **自動進行の実装**: オールイン時の適切な処理
4. **拡張性**: 新しい状態遷移ルールの追加が容易
5. **テスタビリティ**: 各状態遷移を個別にテスト可能

この設計により、複雑なポーカーのゲームフローを堅牢かつ保守しやすい形で実装できています。
