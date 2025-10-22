# ポット計算ドメイン移行ガイド

## 📋 移行の概要

ポット計算ロジックを `DealerService` から `domain/pot_calculator.py` に移行しました。

### 目的
- **責務の分離**: ビジネスルール（ドメイン層）と進行制御（サービス層）を明確に分離
- **テスタビリティ**: `GameState` に依存しない純粋な計算ロジックとして独立
- **再利用性**: ポット計算ロジックを他のサービスからも利用可能に

---

## 🎯 変更内容

### 新規作成ファイル

#### `domain/pot_calculator.py`
```python
PotCalculator        # ポット計算のビジネスロジック
  ├─ create_pots_from_bets()      # ベット額からポット構造を生成
  ├─ calculate_distribution()      # ポット分配を計算
  └─ validate_pot_structure()      # ポット構造の整合性検証

PotDistributor       # ポット分配の実行
  └─ apply_distribution()          # 計算済み分配をスタックに反映
```

### 変更ファイル

#### `services/dealer_service.py`
| メソッド | 変更内容 |
|---------|---------|
| `collect_bets_to_pots()` | **リファクタリング**: `PotCalculator.create_pots_from_bets()` を使用 |
| `distribute_pots()` | **リファクタリング**: `PotCalculator` と `PotDistributor` を使用 |
| `_create_side_pots()` | **非推奨化**: 後方互換性のため残存、内部で `PotCalculator` を呼び出し |
| `calculate_pot_distribution()` | **非推奨化**: 後方互換性のため残存、内部で `PotCalculator` を呼び出し |

---

## 🔄 移行前後の比較

### Before: Services層にビジネスロジックが混在

```python
# dealer_service.py (移行前)
class DealerService:
    def collect_bets_to_pots(self, game):
        # ...100行以上のポット計算ロジック...
        if not all_in_seats:
            # メインポット処理
        else:
            # サイドポット計算
            sorted_bets = sorted(...)
            for seat_index, bet_amount in sorted_bets:
                # 複雑なアルゴリズム
```

**問題点**:
- ❌ ビジネスルールがサービス層に漏出
- ❌ `GameState` に強く依存し、単体テストが困難
- ❌ 他のサービスから再利用できない

### After: ドメイン層に純粋なビジネスロジックとして分離

```python
# pot_calculator.py (移行後)
class PotCalculator:
    @staticmethod
    def create_pots_from_bets(
        bet_contributions: Dict[int, int],
        all_in_seats: List[int],
        existing_pots: List[Pot]
    ) -> List[Pot]:
        """純粋な計算ロジック"""
        # GameStateに依存しない
```

```python
# dealer_service.py (移行後)
class DealerService:
    def collect_bets_to_pots(self, game):
        # データ収集のみ
        bet_contributions = {...}
        all_in_seats = [...]
        
        # ドメインロジックに委譲
        game.table.pots = PotCalculator.create_pots_from_bets(
            bet_contributions, all_in_seats, game.table.pots
        )
```

**改善点**:
- ✅ ビジネスルールがドメイン層に集約
- ✅ 純粋な計算ロジックで単体テストが容易
- ✅ 他のサービスからも再利用可能

---

## 📊 アーキテクチャ図

### Before
```
┌─────────────────────────────────┐
│      DealerService              │
│  ┌──────────────────────────┐   │
│  │ ポット計算ロジック        │   │ ← ビジネスルールが混在
│  │ (100行超)                 │   │
│  └──────────────────────────┘   │
└─────────────────────────────────┘
         ↓
┌─────────────────────────────────┐
│      Domain (Table, Pot)        │
└─────────────────────────────────┘
```

### After
```
┌─────────────────────────────────┐
│      DealerService              │
│  - データ収集                    │
│  - ドメインロジック呼び出し      │
└─────────────────────────────────┘
         ↓ (委譲)
┌─────────────────────────────────┐
│      PotCalculator              │ ← ビジネスルールを集約
│  - create_pots_from_bets()      │
│  - calculate_distribution()     │
│  - validate_pot_structure()     │
└─────────────────────────────────┘
         ↓
┌─────────────────────────────────┐
│      Domain (Table, Pot)        │
└─────────────────────────────────┘
```

---

## 🔧 使用方法

### 1. ポット作成（ベット回収時）

```python
# DealerService.collect_bets_to_pots() 内で使用
from ..domain.pot_calculator import PotCalculator

bet_contributions = {0: 100, 1: 200, 2: 200}  # {seat_index: bet_amount}
all_in_seats = [0]  # オールインした座席

# ドメインロジックでポット構造を計算
game.table.pots = PotCalculator.create_pots_from_bets(
    bet_contributions=bet_contributions,
    all_in_seats=all_in_seats,
    existing_pots=game.table.pots
)
```

### 2. ポット分配（ショーダウン時）

```python
# DealerService.distribute_pots() 内で使用
from ..domain.pot_calculator import PotCalculator, PotDistributor

# ハンドスコアを収集
hand_scores = {
    seat.index: seat.hand_score 
    for seat in game.table.seats 
    if seat.in_hand and hasattr(seat, 'hand_score')
}

in_hand_seats = [seat.index for seat in game.table.seats if seat.in_hand]

# ポット分配を計算
distributions = PotCalculator.calculate_distribution(
    pots=game.table.pots,
    hand_scores=hand_scores,
    in_hand_seats=in_hand_seats
)

# スタックに反映
results = PotDistributor.apply_distribution(
    seats=game.table.seats,
    distributions=distributions
)
```

### 3. ポット構造の検証（デバッグ用）

```python
from ..domain.pot_calculator import PotCalculator

is_valid, error_message = PotCalculator.validate_pot_structure(game.table.pots)
if not is_valid:
    print(f"Invalid pot structure: {error_message}")
```

---

## 🧪 テスト戦略

### ドメインロジックの単体テスト

`tests/test_pot_calculator.py` に以下のテストを実装:

1. **オールインなしの場合**
   - メインポットに全額追加
   - 複数ラウンドの累積

2. **オールインありの場合**
   - 1人オールイン → サイドポット1つ
   - 複数人オールイン → 複数サイドポット

3. **ポット分配**
   - 1人勝ち
   - チョップ（割り切れる/割り切れない）
   - サイドポット分配
   - フォールドプレイヤー除外

4. **整合性検証**
   - 正常なポット構造
   - 負の金額エラー
   - 対象者なしエラー

### 統合テスト

既存の `DealerService` テストは**そのまま動作**します（後方互換性維持）。

---

## 📝 マイグレーションチェックリスト

### 完了項目
- [x] `PotCalculator` クラスの作成
- [x] `PotDistributor` クラスの作成
- [x] `DealerService.collect_bets_to_pots()` のリファクタリング
- [x] `DealerService.distribute_pots()` のリファクタリング
- [x] 後方互換性の維持（非推奨メソッドの残存）
- [x] 単体テストの作成

### 今後の作業
- [ ] `pytest` のインストールと単体テストの実行
- [ ] 統合テストの実行と動作確認
- [ ] 非推奨メソッドの削除（バージョン2.0で予定）
- [ ] パフォーマンスベンチマーク

---

## ⚠️ 注意事項

### 後方互換性

以下のメソッドは**非推奨**ですが、後方互換性のため残されています:

```python
# ❌ 非推奨（内部でPotCalculatorを呼び出し）
dealer_service._create_side_pots(game, bet_contributions, all_in_seats)
dealer_service.calculate_pot_distribution(game)

# ✅ 推奨（直接ドメインロジックを使用）
PotCalculator.create_pots_from_bets(bet_contributions, all_in_seats, existing_pots)
PotCalculator.calculate_distribution(pots, hand_scores, in_hand_seats)
```

将来のバージョンで非推奨メソッドは削除される予定です。

### GameStateへの依存

`PotCalculator` は `GameState` に依存しません。サービス層でデータを収集し、ドメイン層に渡してください。

```python
# ✅ 正しい使い方
bet_contributions = {seat.index: seat.bet_in_round for seat in game.table.seats}
all_in_seats = [seat.index for seat in game.table.seats if seat.status == SeatStatus.ALL_IN]
pots = PotCalculator.create_pots_from_bets(bet_contributions, all_in_seats, existing_pots)

# ❌ 間違った使い方
# PotCalculatorにGameStateを渡さない
```

---

## 🎯 期待される効果

### 1. テスタビリティの向上
- モックなしで純粋な計算ロジックをテスト可能
- テストケースの作成が容易

### 2. 保守性の向上
- ビジネスルールの変更がドメイン層に集約
- サービス層がシンプルになり、可読性向上

### 3. 再利用性の向上
- 他のサービス（AI、リプレイなど）からもポット計算を利用可能
- ポット計算ロジックの一元管理

### 4. デバッグの容易化
- `validate_pot_structure()` でポット構造の整合性を検証
- エラーメッセージが明確

---

## 📚 関連ドキュメント

- [domain/README.md](../app/game/domain/README.md) - ドメイン層の設計思想
- [services/README.md](../app/game/services/README.md) - サービス層の役割
- [STATE_MACHINE_DESIGN.md](../app/game/services/STATE_MACHINE_DESIGN.md) - ゲーム進行の設計

---

## 🤝 貢献

ポット計算ロジックに改善提案がある場合:

1. `tests/test_pot_calculator.py` にテストケースを追加
2. `domain/pot_calculator.py` にロジックを実装
3. プルリクエストを作成

**原則**: ドメイン層は `GameState` に依存してはいけません。
