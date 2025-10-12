# BBオプションを考慮したターン管理のテストコード
from server.app.game.services.turn_manager import TurnManager
from server.app.game.domain.game_state import GameState
from server.app.game.domain.player import Player
from server.app.game.domain.enum import ActionType, Round, SeatStatus

def test_bb_option():
    """BBオプションのテスト"""
    # ゲーム状態とターンマネージャーの初期化
    game = GameState(big_blind=100, small_blind=50)
    turn_manager = TurnManager()
    
    # プレイヤーを作成して着席
    player1 = Player(id="p1", name="Alice")  # SB
    player2 = Player(id="p2", name="Bob")    # BB
    player3 = Player(id="p3", name="Charlie") # UTG
    
    game.table.sit_player(player1, 0, 1000)
    game.table.sit_player(player2, 1, 1000)
    game.table.sit_player(player3, 2, 1000)
    
    # ポジション設定
    game.dealer_seat_index = 2  # Charlieがディーラー
    game.small_blind_seat_index = 0  # AliceがSB
    game.big_blind_seat_index = 1    # BobがBB
    game.current_round = Round.PREFLOP
    
    # ブラインドをポスト
    game.table.seats[0].bet_in_round = 50   # SB
    game.table.seats[1].bet_in_round = 100  # BB
    game.table.seats[1].acted = False       # BBは未行動扱い
    game.current_bet = 100
    
    # UTGがコール
    game.current_seat_index = 2
    game.table.seats[2].bet_in_round = 100
    game.table.seats[2].acted = True
    
    # SBがコール
    game.current_seat_index = 0
    game.table.seats[0].bet_in_round = 100
    game.table.seats[0].acted = True
    
    print("=== BBオプションのテスト ===")
    
    # 次のアクション可能な座席を取得（BBオプション）
    next_seat = turn_manager.get_next_actionable_seat_index(game)
    print(f"次のアクション可能な座席: {next_seat} (期待値: 1 - BBオプション)")
    
    # BBがチェックした場合
    game.table.seats[1].acted = True  # BBがアクション
    
    # ベッティングラウンド完了チェック
    is_complete = turn_manager.is_betting_round_complete(game)
    print(f"ベッティングラウンド完了: {is_complete} (期待値: True)")
    
    print("\n=== レイズがあった場合のBBオプション ===")
    
    # シナリオ2：UTGがレイズした場合
    game2 = GameState(big_blind=100, small_blind=50)
    game2.table.sit_player(player1, 0, 1000)
    game2.table.sit_player(player2, 1, 1000)
    game2.table.sit_player(player3, 2, 1000)
    
    game2.dealer_seat_index = 2
    game2.small_blind_seat_index = 0
    game2.big_blind_seat_index = 1
    game2.current_round = Round.PREFLOP
    
    # ブラインドをポスト
    game2.table.seats[0].bet_in_round = 50
    game2.table.seats[1].bet_in_round = 100
    game2.table.seats[1].acted = False
    game2.current_bet = 100
    
    # UTGがレイズ
    game2.table.seats[2].bet_in_round = 300
    game2.table.seats[2].acted = True
    game2.current_bet = 300
    
    # SBがフォールド
    game2.table.seats[0].status = SeatStatus.FOLDED
    game2.table.seats[0].acted = True
    
    # BBにはオプションがあるか？（レイズがあった場合はBBオプションは適用されない）
    has_bb_option = turn_manager._should_give_bb_option(game2, game2.table.seats[1], 1)
    print(f"レイズ後のBBオプション: {has_bb_option} (期待値: False)")
    
    # 有効なアクションを取得
    valid_actions = turn_manager.get_valid_actions_for_player(game2, "p2")
    print(f"BBの有効なアクション: {[action.value for action in valid_actions]}")

def test_postflop_turn_order():
    """ポストフロップのターン順テスト"""
    print("\n=== ポストフロップのターン順テスト ===")
    
    game = GameState(big_blind=100, small_blind=50)
    turn_manager = TurnManager()
    
    # 3人のプレイヤーを着席
    player1 = Player(id="p1", name="Alice")  # SB
    player2 = Player(id="p2", name="Bob")    # BB  
    player3 = Player(id="p3", name="Charlie") # Button
    
    game.table.sit_player(player1, 0, 1000)
    game.table.sit_player(player2, 1, 1000)
    game.table.sit_player(player3, 2, 1000)
    
    game.dealer_seat_index = 2
    game.small_blind_seat_index = 0
    game.big_blind_seat_index = 1
    game.current_round = Round.FLOP  # フロップ
    
    # フロップでの最初のアクター設定
    turn_manager.set_first_actor_for_round(game)
    print(f"フロップの最初のアクター: {game.current_seat_index} (期待値: 0 - SB)")
    
    # ターン順の確認
    game.current_seat_index = 0
    next_seat = turn_manager.get_next_actionable_seat_index(game)
    print(f"SBの次: {next_seat} (期待値: 1 - BB)")
    
    game.current_seat_index = 1
    next_seat = turn_manager.get_next_actionable_seat_index(game)
    print(f"BBの次: {next_seat} (期待値: 2 - Button)")

if __name__ == "__main__":
    test_bb_option()
    test_postflop_turn_order()