# AIService 使用ガイド

## 概要
`AIService`はテキサスホールデムのAIプレイヤーのアクション決定を行うサービスです。

## アクション決定の優先順位
1. **コール (CALL)**: 可能な場合は常にコール
2. **チェック (CHECK)**: コールできない場合でチェック可能ならチェック
3. **フォールド (FOLD)**: それ以外はフォールド

## 基本的な使い方

```python
from app.game.services import AIService
from app.game.domain.game_state import GameState

# AIサービスのインスタンス化
ai_service = AIService()

# ゲーム状態とAIプレイヤーの座席を渡してアクションを決定
action = ai_service.decide_action(game, ai_player_seat)

# アクションを実行
if action:
    await action_service.execute_action(game, action)
```

## PokerEngineやGameServiceとの統合例

```python
from app.game.services import PokerEngine, AIService

class PokerEngine:
    def __init__(self):
        self.ai_service = AIService()
        # ... 他の初期化
    
    async def process_action(self, game: GameState, action: PlayerAction) -> bool:
        # プレイヤーのアクション処理
        result = await self.action_service.execute_action(game, action)
        
        if result:
            # ターンを進める
            self._move_to_next_player(game)
            
            # 次のプレイヤーがAIかチェック
            if game.current_seat_index is not None:
                current_seat = game.table.seats[game.current_seat_index]
                if current_seat.is_occupied and current_seat.player.name.startswith("AI"):
                    # AIのアクションを自動実行
                    ai_action = self.ai_service.decide_action(game, current_seat)
                    if ai_action:
                        await asyncio.sleep(1)  # 少し待ってから実行（リアルっぽく）
                        await self.process_action(game, ai_action)
        
        return result
```

## WebSocket統合例

```python
from fastapi import WebSocket
from app.game.services import GameService, AIService

ai_service = AIService()

@router.websocket("/ws/game/{game_id}")
async def game_websocket(websocket: WebSocket, game_id: str):
    # ... 接続処理
    
    async def handle_player_action(data: dict):
        # プレイヤーのアクション処理
        success = await game_service.process_player_action(
            game_id, player_id, action_type, amount
        )
        
        if success:
            # 状態をブロードキャスト
            await broadcast_game_state(game_id)
            
            # AIのターンをチェック
            game = game_service.get_game_state(game_id)
            if game and game.current_seat_index is not None:
                current_seat = game.table.seats[game.current_seat_index]
                
                if ai_service.should_ai_act(game, current_seat.player.id):
                    # 少し待ってからAIのアクションを実行
                    await asyncio.sleep(1.5)
                    
                    ai_action = ai_service.decide_action(game, current_seat)
                    if ai_action:
                        await game_service.poker_engine.process_action(game, ai_action)
                        await broadcast_game_state(game_id)
```

## メソッド詳細

### `decide_action(game: GameState, seat: Seat) -> Optional[PlayerAction]`
AIのアクションを決定します。

**引数:**
- `game`: ゲーム状態
- `seat`: AIプレイヤーの座席

**戻り値:**
- 決定されたアクション（PlayerAction）

### `should_ai_act(game: GameState, player_id: str) -> bool`
指定されたプレイヤーがAIで、かつアクションすべきタイミングかチェックします。

**引数:**
- `game`: ゲーム状態
- `player_id`: プレイヤーID

**戻り値:**
- AIがアクションすべきならTrue

## 注意点

1. **AIプレイヤーの判定**: 現在は名前が "AI" で始まるプレイヤーをAIとして扱います
2. **オールイン**: スタックが足りない場合は自動的にオールイン扱いでコールします
3. **非同期処理**: WebSocketと組み合わせる場合は、適切に`await`を使用してください
4. **遅延実行**: リアルな体験のため、AIのアクション前に少し待つことを推奨します（1〜2秒）

## 今後の拡張案

- ハンド強度に基づいたベット/レイズの判断
- ポット額やスタックサイズを考慮した戦略
- プリフロップ、フロップ以降で異なる戦略
- 複数の難易度レベル（保守的、アグレッシブなど）
