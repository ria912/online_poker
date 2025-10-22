# Domain 層 - テキサスホールデム・ポーカーエンジン

**目標**: シングルプレイ（1人プレイヤー vs AI）のリアルタイムWebアプリ  
**設計原則**: 純粋なビジネスロジック層。外部I/O・UI・通信は含まず、ポーカーのルールと状態遷移のみを担当

---

## 📐 設計思想

### コア原則
- **単一責任**: 各クラスは1つの概念（座席/テーブル/デッキ/状態）に専念
- **不変条件の保護**: スタック≥0、ホールカード=2枚などをクラス内で強制
- **集約ルート**: `GameState` が全体の整合性を保証
- **副作用の隔離**: ランダム性（シャッフル）・通知はサービス層が担当
- **支払い処理の一元化**: `Seat.pay()` でスタック操作を統一管理

### Services層との責任分離
| 層 | 責任 |
|---|---|
| **Domain** | 「何が正しい状態か」を定義・検証 |
| **Services** | 「いつ・どの順序で実行するか」を制御 |

---

## 📦 ファイル構成

### `enum.py` - 列挙型定義
**全ての状態・アクション・ポジションを型安全に表現**

```python
Round: PREFLOP → FLOP → TURN → RIVER → SHOWDOWN
SeatStatus: EMPTY | ACTIVE | FOLDED | ALL_IN | SITTING_OUT
ActionType: FOLD | CHECK | CALL | BET | RAISE | ALL_IN
Position: SB | BB | LJ | HJ | CO | BTN
GameStatus: WAITING | IN_PROGRESS | ROUND_OVER | BETTING_OVER | HAND_COMPLETE
```

---

### `player.py` - プレイヤーエンティティ
**最小情報のみ保持（座席・スタックは `Seat` が管理）**

```python
class Player:
    id: str          # 一意識別子
    name: str        # 表示名
    is_ai: bool      # AI判定フラグ
```

**シングルプレイ拡張案:**
```python
ai_difficulty: str = "medium"  # easy/medium/hard
ai_personality: str = "balanced"  # tight/loose/aggressive
```

---

### `deck.py` - カード・デッキ
**52枚のカード管理とtreys評価器との連携**

```python
class Card:
    rank: str  # "23456789TJQKA"
    suit: str  # "shdc" (♠♥♦♣)
    
    to_treys_int() -> int  # treys評価器用の変換

class Deck:
    cards: List[Card]  # 52枚のカード
    
    shuffle() -> None
    draw(n: int) -> List[Card]
```

**重要**: デッキは重複を許さず、引いたカードは自動削除

---

### `action.py` - アクション値オブジェクト
**不変のアクション記録**

```python
@dataclass(frozen=True)
class PlayerAction:
    player_id: str
    action_type: ActionType
    amount: int = 0
```

---

### `seat.py` - 座席管理 ⭐
**各座席の状態とスタック操作の中核**

#### 主要プロパティ
```python
index: int                    # 座席番号
player: Optional[Player]      # 着席者
stack: int                    # 残りチップ
hole_cards: List[Card]        # ホールカード（2枚）
position: Optional[Position]  # ポジション（SB/BB/BTN等）
status: SeatStatus            # EMPTY/ACTIVE/FOLDED/ALL_IN/SITTING_OUT

bet_in_round: int             # 現ラウンドのベット累計
bet_in_hand: int              # 現ハンド全体のベット累計
last_action: Optional[ActionType]
acted: bool                   # 現ラウンドで行動済みか
hand_score: int               # 役評価スコア（小さいほど強い）
show_hand: bool               # ショーダウンで公開するか
```

#### 重要メソッド
```python
pay(amount: int) -> int:
    """
    支払い処理の唯一の入口
    - 実際に支払える額を返却（スタック不足時は全額）
    - stack, bet_in_round, bet_in_handを同時更新
    - 整合性を保証
    """

refund(amount: int):
    """払い戻し処理"""

sit_down(player: Player, stack: int):
    """プレイヤーを着席"""

stand_up():
    """プレイヤーを退席"""

receive_cards(cards: List[Card]):
    """ホールカードを受け取る（2枚必須）"""

clear_for_new_hand():
    """新ハンド開始時のリセット"""

reset_for_new_round():
    """新ラウンド開始時のリセット（bet_in_round=0）"""
```

#### プロパティ
```python
is_occupied: bool   # プレイヤーが座っている
is_active: bool     # アクション可能（ACTIVE かつ stack>0）
in_hand: bool       # ハンドに参加中（ACTIVE or ALL_IN）
```

---

### `table.py` - テーブル管理
**共有状態（コミュニティカード・ポット・座席配列）**

#### 構造
```python
class Pot:
    amount: int                  # ポット額
    eligible_seats: List[int]    # このポットの対象座席

class Table:
    deck: Deck
    seats: List[Seat]            # 座席配列
    community_cards: List[Card]  # コミュニティカード（最大5枚）
    pots: List[Pot]              # メインポット + サイドポット群
```

#### メソッド
```python
reset_for_new_hand():
    """新ハンド用にデッキ・カード・ポットをリセット"""

reset_for_new_round():
    """新ラウンド用に各座席のbet_in_roundをリセット"""

sit_player(player, seat_index):
    """指定座席にプレイヤーを着席"""

stand_player(seat_index):
    """指定座席から退席"""

in_hand_seats() -> List[Seat]:
    """ハンド参加中の座席（ACTIVE or ALL_IN）"""

active_seats() -> List[Seat]:
    """アクション可能な座席（ACTIVE のみ）"""

empty_seats() -> List[int]:
    """空席のインデックス一覧"""
```

#### プロパティ
```python
total_pot: int          # 全ポットの合計額
is_hand_over: bool      # ハンド終了判定（in_hand が1人以下）
is_betting_over: bool   # ベッティング終了判定（active が1人以下）
```

---

### `game_state.py` - ゲーム状態（集約ルート）⭐
**ハンド全体の進行状態を一元管理**

#### 主要プロパティ
```python
id: str                            # ゲームセッションID
status: GameStatus                 # WAITING/IN_PROGRESS/HAND_COMPLETE
current_round: Round               # PREFLOP/FLOP/TURN/RIVER/SHOWDOWN

table: Table                       # テーブル参照
players: List[Player]              # 全プレイヤー（着席/未着席含む）
history: List[PlayerAction]        # アクション履歴

# ブラインド・ベット設定
big_blind: int                     # BBサイズ
small_blind: int                   # SBサイズ
current_bet: int                   # 現ラウンドの最大ベット額
min_raise_amount: int              # 最小レイズ額（総額）
last_raise_delta: int              # 最後のレイズ幅

# ポジション
dealer_seat_index: Optional[int]   # ディーラーボタン
small_blind_seat_index: Optional[int]
big_blind_seat_index: Optional[int]
current_seat_index: Optional[int]  # 現在のアクション権
last_aggressive_actor_index: Optional[int]  # 最後にBET/RAISEした座席

# 結果
winners: List[Dict]                # 勝者リスト
valid_actions: List[Dict]          # 現在の有効アクション
```

#### メソッド
```python
add_player(player: Player):
    """プレイヤーをセッションに追加"""

remove_player_by_id(player_id: str):
    """プレイヤーをセッションから削除（着席中なら退席も実行）"""

get_player_by_id(player_id: str) -> Optional[Player]:
    """IDでプレイヤー検索"""

add_action(player_id, action_type, amount):
    """アクションを履歴に追加"""

clear_for_new_hand():
    """新ハンド開始時の初期化"""

clear_for_new_round():
    """新ラウンド開始時の初期化"""
```

---

## 🔄 状態遷移フロー

### 新ハンド開始
```
1. GameState.clear_for_new_hand()
   ↓
2. Table.reset_for_new_hand()
   ↓
3. 各Seat.clear_for_new_hand()
   ↓
4. [Services層] ディーラーボタン回転・ブラインド設定
   ↓
5. [Services層] Seat.pay() でブラインド徴収
   ↓
6. [Services層] ホールカード配布 Seat.receive_cards()
```

### ベットラウンド
```
1. プレイヤーアクション
   ↓
2. Seat.pay() でベット実行
   ↓
3. GameState.current_bet 更新
   ↓
4. 次のプレイヤーへ
   ↓
5. 全員acted=True → ラウンド終了
```

### ラウンド終了
```
1. [Services] DealerService.collect_bets_to_pots()
   - オールインなし → メインポットに追加
   - オールインあり → サイドポット作成
   ↓
2. Table.reset_for_new_round()
   ↓
3. 各Seat.reset_for_new_round()
   ↓
4. コミュニティカード配布（FLOP/TURN/RIVER）
```

### ショーダウン
```
1. [Services] HandEvaluator で役評価
   ↓
2. Seat.hand_score に結果格納
   ↓
3. [Services] DealerService.calculate_pot_distribution()
   ↓
4. 勝者にチップ分配
   ↓
5. GameState.status = HAND_COMPLETE
```

---

## ⚠️ 不変条件・整合性ルール

### 必ず守るべき制約
1. ホールカードは常に2枚（0枚または2枚のみ許可）
2. デッキに重複カードは存在しない
3. `stack` は常に ≥ 0
4. `SeatStatus.EMPTY` ⇔ `player is None`
5. `bet_in_round` はラウンド切替時に0にリセット
6. **スタック操作は必ず `Seat.pay()` を経由**

### ポット管理の整合性（重要）
- **オールインなし**: メインポットに追加（既存ポットを保持）
- **オールインあり**: サイドポット作成（既存ポットは維持）
- **ラウンドごとにポットをクリアしない**

---

## 🎮 シングルプレイWebアプリ向け拡張指針

### 1. AI戦略の多様化
```python
# player.py
class Player:
    ai_difficulty: str = "medium"  # easy/medium/hard
    ai_personality: str = "balanced"  # tight/loose/aggressive/maniac
    
# services層でAI判断に使用
def ai_decide_action(player: Player, game: GameState) -> ActionType:
    if player.ai_difficulty == "easy":
        # ランダム戦略
    elif player.ai_difficulty == "hard":
        # GTO近似戦略
```

### 2. アニメーション・UI制御
```python
# game_state.py
class GameState:
    animation_speed: float = 1.0  # 0.5-2.0
    auto_action_delay: float = 1.5  # AI行動の遅延（秒）
    show_ai_thinking: bool = True
```

### 3. 統計・履歴トラッキング
```python
# seat.py
class SeatStatistics:
    hands_played: int = 0
    vpip: float = 0.0  # Voluntarily Put In Pot
    pfr: float = 0.0   # Pre-Flop Raise
    aggression_factor: float = 0.0
    
# game_state.py
hand_history: List[Dict] = []  # リプレイ用の全アクション記録
```

### 4. チュートリアル・ヒント機能
```python
# services層
def suggest_action(game: GameState, seat: Seat) -> Dict:
    """初心者向けの推奨アクション計算"""
    pot_odds = calculate_pot_odds(game)
    return {
        "action": ActionType.CALL,
        "reason": "good_pot_odds",
        "confidence": 0.75,
        "explanation": "ポットオッズが有利です"
    }
```

### 5. リアルタイム通信用のイベント
```python
# services層からWebSocketへ送信するイベント
{
    "type": "game_state_update",
    "round": "FLOP",
    "current_seat": 1,
    "pot": 300,
    "community_cards": ["A♠", "K♥", "Q♦"]
}
```

---

## 🛠️ Services層開発のガイドライン

### Services層が担当すること
1. **進行制御**: ハンド・ラウンドの開始/終了タイミング
2. **AI判断**: AIプレイヤーのアクション決定
3. **役評価**: treys等を使った役判定
4. **通知送信**: WebSocket経由でクライアントに状態通知
5. **タイマー管理**: AIの思考時間・タイムアウト処理

### Domainを呼び出す際の注意
```python
# ✅ 正しい使い方
seat.pay(amount)  # スタック操作は必ずpay()経由

# ❌ 間違った使い方
seat.stack -= amount  # 直接変更は禁止（整合性が壊れる）
seat.bet_in_round += amount
```

### ポット管理の正しい実装
```python
# ✅ 正しい（dealer_service.py参照）
def collect_bets_to_pots(game: GameState):
    if not all_in_seats:
        # メインポットに追加（既存を保持）
        game.table.pots[0].amount += total_bets
    else:
        # サイドポット作成（既存を保持）
        self._create_side_pots(...)

# ❌ 間違い
game.table.pots = []  # 毎回クリアすると過去のポットが消える
```

---

## 📖 学習推奨順序

### Step 1: 基本概念の理解
1. `enum.py` - 用語・状態定義
2. `player.py` - プレイヤーの最小情報
3. `deck.py` - カード表現

### Step 2: 状態管理の理解
4. `seat.py` - 座席の状態と `pay()` の重要性
5. `table.py` - 座席の集合とポット管理
6. `action.py` - アクションの記録

### Step 3: 全体像の把握
7. `game_state.py` - 集約ルートとして全体を統合

### Step 4: Services層へ
この順序で読めば、Services層のコード（`dealer_service.py`、`game_service.py`等）の意図が理解できます。

---

## 🎯 開発目標の達成チェックリスト

- [ ] 1人プレイヤー vs 複数AI の対戦実装
- [ ] リアルタイムWebSocket通信
- [ ] フロントエンドへの状態同期
- [ ] AIの自動アクション（遅延付き）
- [ ] アニメーション対応
- [ ] ハンド履歴・統計表示
- [ ] チュートリアル・ヒント機能
- [ ] レスポンシブUI（スマホ対応）

---

**このREADMEは、Services層開発時にAIに渡すことで、Domain層の設計意図と使用方法を正確に伝えることを目的としています。**