# Services 層（学習用ガイド）

このフォルダは、ドメインを組み合わせて「ゲーム進行」を実現するアプリケーションロジックをまとめます。乱数（配布）、アクターの選定、入力検証、状態遷移の編成、通知トリガーなどを担当します。外部I/Oの詳細（DB/ネットワーク）はここでは扱いません。

---

## 設計思想（Principles）

- **オーケストレーション**: いつ何をするかの順序を決め、ドメインの操作を組み立てる
- **ドメインの尊重**: ルールの真実は `domain/` にある。サービスはルールを破らないよう補助・整合化する
- **副作用の集約**: シャッフルや配布、アクション適用、フロー制御はサービス側で完結させる
- **スタック操作の統一**: `Seat.pay()` メソッドを使用して支払い処理を一元化
- **単純化されたAPI**: 座席インデックスベースの操作で高速化とシンプル化を実現
- **テスタビリティ**: できる限り純粋な計算で書き、依存は注入可能にする

---

## ファイル一覧と役割

### `game_service.py`
ゲームセッションのライフサイクル管理の最上位サービス。
- ゲーム作成・参加・開始・アクション委譲を担当
- 外部インターフェース（WebSocket/REST API）の窓口
- ゲーム状態の一元管理（`games: Dict[str, GameState]`）

**主要API**:
- `create_game(game_id, big_blind)` → `GameState`
- `join_game(game_id, player)` → `bool`
- `start_game(game_id)` → `bool`
- `process_player_action(game_id, player_id, action_type, amount)` → `bool`
- `get_game_state(game_id)` → `GameState | None`
- `get_valid_actions(game_id, player_id)` → `List[ActionType]`

### `poker_engine.py`
コア進行のオーケストレータ。各専門サービスを統合してハンド全体を制御。
- 新ハンド開始、アクション処理、ラウンド遷移、ショーダウン進行を束ねる
- `HandService`, `ActionService`, `TurnManager`, `DealerService` を協調させる
- プレイヤーID → 座席検索のヘルパーメソッド提供
- **ステートマシン**: `process_action` がゲーム状態遷移を一元管理

**主要API**:
- `start_new_hand(game)` → `bool`
- `process_action(game, PlayerAction)` → `bool`: ステートマシンとして機能
- `seat_player(game, player, seat_index, buy_in)` → `bool`
- `get_valid_actions(game, player_id)` → `List[ActionType]`

**内部メソッド（ステートマシン）**:
- `_advance_to_next_street(game)`: 次のストリートへ進む（カード配布とターンセットアップ）
- `_check_and_run_it_out(game)`: 自動進行(Run it out)の判定と実行
- `_proceed_to_fold_win(game)`: フォールド勝ちの処理
- `_proceed_to_showdown(game)`: ショーダウン処理
- `_is_valid_action(game, action)`: アクション検証

**ステートマシンの動作**:
`process_action` は以下の順序でゲーム状態を判断・遷移します:
1. アクション実行
2. 次のアクターに進む → ラウンド継続ならここで終了
3. ベット回収（ラウンド終了時）
4. フォールド勝ちチェック → 該当すれば終了
5. リバーベッティング終了チェック → 該当すればショーダウン
6. 次のストリートに進む
7. 自動進行チェック → アクティブプレイヤーが1人以下ならリバーまで自動進行

**自動進行(Run it out)の実装**:
アクション不要（`active_seats <= 1`）かつショーダウン必要（`in_hand_seats > 1`）の場合、
`_check_and_run_it_out` が自動的にリバーまでカードを配布してショーダウンに進みます。
これにより、複数人がオールインした状態を正しく処理できます。

### `dealer_service.py`
ディーラー責務を担当。
- ボタン回転、ブラインド設定、カード配布、ベット回収を実行
- **重要**: `Seat.pay()` を使用してブラインド徴収を実装

**主要API**:
- `setup_new_hand(game)` → `bool`: ハンド開始の一括セットアップ
- `rotate_dealer_button(game)`: ボタン位置更新
- `set_blind_positions(game)`: SB/BB位置決定（ヘッズアップ対応）
- `collect_blinds(game)`: ブラインド徴収（`Seat.pay()` 使用）
- `deal_hole_cards(game)`: ホールカード配布
- `deal_community_cards(game, round_type)`: フロップ/ターン/リバー配布
- `collect_bets_to_pots(game)`: ラウンド終了時のポット回収（サイドポット対応）
- `calculate_pot_distribution(game)` → `List[dict]`: ポット分配計算

### `turn_manager.py`
アクター選定とラウンド完了判定を担当。
- 最初のアクター設定、次アクター算出を提供
- **座席インデックスベース**の高速な有効アクション判定

**主要API**:
- `start_round(game)`: 新ラウンド開始とアクター設定
- `advance_turn(game)` → `bool`: 次のアクターに進む（False: ラウンド完了）
- `get_valid_actions(game, seat_index)` → `List[ActionType]`: 有効アクション取得

**内部メソッド**:
- `_find_next_actionable_seat(game)`: 次の行動可能座席を検索
- `_is_round_complete(game)`: ラウンド完了判定
- `_get_next_active_seat(game, current_index)`: 次のアクティブ座席

### `action_service.py`
ベッティングアクションの適用と詳細検証を担当。
- `FOLD/CHECK/CALL/BET/RAISE` の状態変更を一元化
- **重要**: `Seat.pay()` メソッドを使用して全ての支払い処理を実装
- レイズ後の行動フラグリセット処理

**主要API**:
- `execute_action(game, action)` → `bool`: アクション実行
- `is_valid_action(game, action)` → `bool`: アクション検証

**実装詳細**:
- `CALL`: `seat.pay(call_amount)` で支払い
- `BET`: `seat.pay(action.amount)` で支払い
- `RAISE`: `seat.pay(raise_amount)` で支払い
- オールイン検出: `seat.stack == 0` で自動設定
- レイズ後リオープン: `_reset_acted_flags_after_raise()` で他プレイヤーの `acted` をリセット

### `hand_service.py`
ショーダウン用のハンド評価と勝者確定を担当。
- `HandEvaluator` を使用してハンド評価を実行
- ポット毎の勝者を決定し、分配情報を返却

**主要API**:
- `evaluate_showdown(game)` → `List[winner_info]`: ショーダウン評価とポット分配

### `hand_evaluator.py`
最小APIのハンド評価（treys Evaluator を使用）。
- `evaluate_hand(hole_cards, community_cards)` → `int`: ハンドスコア取得
- `get_hand_name(score)` → `str`: 役名取得

---

## 典型フロー

### 1. ゲーム作成と参加
```python
game_service = GameService()
game = await game_service.create_game("game_1", big_blind=100)
await game_service.join_game("game_1", player1)
await game_service.join_game("game_1", player2)
```

### 2. ハンド開始
```python
await game_service.start_game("game_1")
# ↓ PokerEngine.start_new_hand() が呼ばれる
# ↓ Table.reset_for_new_hand()
# ↓ DealerService.setup_new_hand()
#   - rotate_dealer_button()
#   - set_blind_positions()
#   - deal_hole_cards()
#   - collect_blinds() → Seat.pay() 使用
# ↓ TurnManager.start_round() → 最初のアクター設定
```

### 3. アクション処理（ステートマシン）
```python
await game_service.process_player_action("game_1", "player_1", ActionType.CALL)
# ↓ PokerEngine.process_action() がステートマシンとして動作
# ↓ (1) ActionService.execute_action() → Seat.pay() 使用
# ↓ (2) TurnManager.advance_to_next_actor()
# ↓ (3) ラウンド継続 → 終了、ラウンド終了 → (4)以降へ
# ↓ (4) DealerService.collect_bets_to_pots()
# ↓ (5) フォールド勝ちチェック → 該当なら _proceed_to_fold_win()
# ↓ (6) リバーベッティング終了チェック → 該当なら _proceed_to_showdown()
# ↓ (7) _advance_to_next_street()
#   - DealerService.deal_community_cards()
#   - TurnManager.reset_for_new_round()
#   - TurnManager.set_first_actor_for_round()
# ↓ (8) _check_and_run_it_out()
#   - active_seats <= 1 かつ in_hand_seats > 1 の場合
#   - リバーまで自動進行 → _proceed_to_showdown()
```

### 4. ショーダウン
```python
# ↓ 最終ラウンド完了 → _proceed_to_showdown()
# ↓ HandService.evaluate_showdown()
#   - 各プレイヤーのハンドを評価
#   - DealerService.calculate_pot_distribution()
#   - 勝者スタックに加算
# ↓ game.status = GameStatus.HAND_COMPLETE
```

---

## 責務境界のルール

- **ドメイン**: 状態と制約（`Seat.pay()` でスタック整合性保証）
- **サービス**: 進行と副作用（配布順序、アクター選定、通知タイミング）
- **スタック操作**: 必ず `Seat.pay()` を経由（ActionService, DealerService）
- **ステートマシン**: `PokerEngine.process_action` がゲーム状態遷移を一元管理
- **自動進行**: アクティブプレイヤーが1人以下の場合、リバーまで自動進行してショーダウン
- **検証の多層化**:
  1. `TurnManager`: 基本的な順番・状態チェック
  2. `ActionService`: アクション固有の詳細検証
  3. `PokerEngine`: 全体的な整合性確認

---

## リアルタイムシングルプレイ向け推奨拡張

### 1. AI対戦サービス（AIOpponentService）
```python
class AIOpponentService:
    """AI対戦相手の思考・行動を管理"""
    
    async def decide_action(
        self, 
        game: GameState, 
        seat_index: int,
        difficulty: str = "medium"
    ) -> PlayerAction:
        """AI思考ロジック"""
        # 難易度別の戦略
        # - easy: ランダム・パッシブ
        # - medium: ポットオッズ・ポジション考慮
        # - hard: GTO近似・レンジ戦略
        pass
    
    def calculate_thinking_delay(self, difficulty: str) -> float:
        """人間らしい思考時間を計算"""
        return random.uniform(0.5, 2.0)
```

### 2. ゲーム速度制御サービス（GameSpeedService）
```python
class GameSpeedService:
    """アニメーションとタイミングを制御"""
    
    async def animate_deal(
        self, 
        game: GameState,
        speed_multiplier: float = 1.0
    ):
        """カード配布アニメーション"""
        delay = 0.3 / speed_multiplier
        # WebSocketで段階的に送信
    
    async def animate_pot_award(
        self,
        winners: List[dict],
        speed_multiplier: float = 1.0
    ):
        """ポット分配アニメーション"""
        pass
```

### 3. 統計トラッキングサービス（StatisticsService）
```python
class StatisticsService:
    """プレイヤー統計の計算と保存"""
    
    def update_vpip(self, player_id: str, voluntarily_put: bool):
        """VPIP統計更新"""
        pass
    
    def calculate_aggression_factor(
        self, 
        player_id: str
    ) -> float:
        """アグレッションファクター計算"""
        # (Bets + Raises) / Calls
        pass
    
    def get_session_summary(
        self, 
        player_id: str
    ) -> Dict:
        """セッションサマリー取得"""
        return {
            "hands_played": 50,
            "win_rate": 0.24,
            "biggest_pot": 1500,
            "profit": 350
        }
```

### 4. チュートリアルサービス（TutorialService）
```python
class TutorialService:
    """初心者向けヒントと推奨アクション"""
    
    def suggest_action(
        self,
        game: GameState,
        seat: Seat
    ) -> Dict:
        """推奨アクションを計算"""
        pot_odds = self._calculate_pot_odds(game, seat)
        hand_strength = self._estimate_hand_strength(seat, game)
        
        return {
            "action": ActionType.CALL,
            "reason": "pot_odds_favorable",
            "pot_odds": pot_odds,
            "hand_strength": hand_strength,
            "confidence": 0.75,
            "explanation": "ポットオッズが有利です（3:1）"
        }
    
    def get_situation_hint(
        self,
        game: GameState,
        seat: Seat
    ) -> str:
        """状況説明を生成"""
        return "あなたはボタン位置です。ポジションアドバンテージを活かしましょう。"
```

### 5. リプレイサービス（ReplayService）
```python
class ReplayService:
    """ハンド履歴の記録と再生"""
    
    def record_hand(self, game: GameState):
        """ハンドを記録"""
        hand_data = {
            "hand_id": generate_id(),
            "players": [...],
            "actions": game.history,
            "community_cards": game.table.community_cards,
            "pots": game.table.pots,
            "winners": game.winners
        }
        # DBに保存
    
    async def replay_hand(
        self,
        hand_id: str,
        speed_multiplier: float = 1.0
    ):
        """ハンドをリプレイ"""
        # 段階的にWebSocketで送信
        pass
```

### 6. イベント通知サービス（EventService）
```python
class EventService:
    """ゲームイベントの発行と管理"""
    
    async def emit_action(
        self,
        game_id: str,
        action: PlayerAction
    ):
        """アクションイベント発行"""
        await websocket_manager.broadcast(game_id, {
            "type": "player_action",
            "player_id": action.player_id,
            "action": action.action_type,
            "amount": action.amount
        })
    
    async def emit_round_change(
        self,
        game_id: str,
        new_round: Round,
        community_cards: List[Card]
    ):
        """ラウンド変更イベント発行"""
        pass
```

### 7. セッション管理サービス（SessionService）
```python
class SessionService:
    """マルチテーブル・セッション管理"""
    
    def create_session(self, player_id: str) -> str:
        """プレイヤーセッション作成"""
        pass
    
    def join_table(
        self,
        session_id: str,
        game_id: str
    ) -> bool:
        """テーブルに参加"""
        pass
    
    def switch_table(
        self,
        session_id: str,
        from_game_id: str,
        to_game_id: str
    ):
        """テーブル切替"""
        pass
```

---

## アーキテクチャ推奨パターン

### レイヤー構成
```
WebSocket/REST API
    ↓
GameService（エントリーポイント）
    ↓
PokerEngine（オーケストレータ）
    ↓
専門サービス（Dealer, Turn, Action, Hand）
    ↓
Domain Layer（ルールの真実）
```

### 非同期処理のポイント
```python
# AI思考時間のシミュレーション
async def process_ai_turn(game: GameState, ai_seat: Seat):
    thinking_time = ai_service.calculate_thinking_delay("medium")
    await asyncio.sleep(thinking_time)
    action = await ai_service.decide_action(game, ai_seat.index)
    await poker_engine.process_action(game, action)
```

### イベント駆動設計
```python
# オブザーバーパターンの活用
class GameEventObserver:
    async def on_action_executed(self, game: GameState, action: PlayerAction):
        await event_service.emit_action(game.game_id, action)
        await statistics_service.update_stats(action)
        
    async def on_round_changed(self, game: GameState):
        await event_service.emit_round_change(...)
        await animation_service.animate_deal(...)
```

---

## テストの観点

### ユニットテスト
- `TurnManager`: アクター選定、ラウンド完了判定
- `DealerService`: 配布・ポット回収（`Seat.pay()` との統合）
- `ActionService`: 各アクション適用（`Seat.pay()` の正確性）

### 統合テスト
- プリフロップからショーダウンまでの一連進行（2-3人）
- サイドポット計算（複数オールイン）
- ヘッズアップ特則（SB/BB位置）

### シナリオテスト
- AI対戦の完全なゲームフロー
- リプレイ機能の記録・再生
- マルチテーブルの並行処理

---

## 拡張指針（一般）

- **設定の外部化**: ブラインド構造、テーブルサイズ、タイムバンクを設定ファイル化
- **プラグイン機構**: AI戦略、評価器、ルールバリアントを差し替え可能に
- **パフォーマンス**: 座席インデックスベースの処理で高速化（現在実装済み）
- **ロギング**: 詳細なゲームログでデバッグとリプレイを支援
