from typing import Optional, List, Dict, Any
from ..domain.game_state import GameState
from ..domain.player import Player
from ..domain.seat import Seat
from ..domain.action import PlayerAction
from ..domain.enum import ActionType, GameStatus, Round
from .hand_service import HandService
from .action_service import ActionService
from .turn_manager import TurnManager
from .dealer_service import DealerService

class PokerEngine:
    """ポーカーの核となるゲームロジック"""
    
    def __init__(self):
        self.hand_service = HandService()
        self.action_service = ActionService()
        self.turn_manager = TurnManager()
        self.dealer_service = DealerService()
    
    def start_new_hand(self, game: GameState) -> bool:
        """新しいハンドを開始"""
        active_seats = [seat for seat in game.table.seats if seat.is_active]
        if len(active_seats) < 2:
            return False
        
        # テーブル状態をリセット
        game.table.reset_for_new_hand()
        
        # DealerServiceで新ハンドセットアップ
        if not self.dealer_service.setup_new_hand(game):
            return False
        
        # ゲーム状態を更新
        game.status = GameStatus.IN_PROGRESS
        game.current_round = Round.PREFLOP
        
        # 最初のアクター設定
        self.turn_manager.set_first_actor_for_round(game)
        
        return True

    async def process_action(self, game: GameState, action: PlayerAction) -> bool:
        """
        プレイヤーアクションを処理し、ゲーム状態を進める
        ステートマシンとして機能し、次の状態を判断する
        """
        if not self._is_valid_action(game, action):
            return False
        
        # (1) アクションを実行
        success = await self.action_service.execute_action(game, action)
        if not success:
            return False
        
        game.history.append(action)
        
        # (2) 次のアクターに進むか確認
        round_continues = self.turn_manager.advance_to_next_actor(game)
        
        if round_continues:
            # ラウンド継続 (次のプレイヤーのアクション待ち)
            return True
        
        # (3) ベッティングラウンド終了
        # (これ以降、round_continues == False)
        
        # (3a) ベットをポットに回収
        # (ラウンド終了時は必ずベットを回収する)
        self.dealer_service.collect_bets_to_pots(game)

        # (3b) フォールド勝ちか?
        if len(game.table.in_hand_seats()) <= 1:
            return self._proceed_to_fold_win(game)

        # (3c) リバーのベッティング終了か?
        if game.current_round == Round.RIVER:
            self._proceed_to_showdown(game)
            return True
            
        # (3d) 次のストリートへ (Flop, Turn, River)
        self._advance_to_next_street(game)
        
        # (4) 自動進行 (Run it out) のチェック
        # (次のストリートに進んだ結果、アクション不要かチェック)
        return self._check_and_run_it_out(game)

    
    def seat_player(
        self, 
        game: GameState, 
        player: Player, 
        seat_index: Optional[int] = None,
        buy_in: int = 10000
    ) -> bool:
        """プレイヤーを座席に配置"""
        # 空席を探す
        if seat_index is None:
            empty_seats = game.table.empty_seats()
            if not empty_seats:
                return False
            seat_index = empty_seats[0]
        
        # 座席が有効かチェック
        if not (0 <= seat_index < len(game.table.seats)):
            return False
        
        seat = game.table.seats[seat_index]
        if seat.is_occupied:
            return False
        
        # Seatのsit_downメソッドを使用
        seat.sit_down(player, buy_in)
        
        # ゲームのプレイヤーリストに追加
        if player not in game.players:
            game.players.append(player)
        
        return True
    
    def get_valid_actions(self, game: GameState, player_id: str) -> List[Dict[str, Any]]:
        """プレイヤーの有効なアクションを取得（リッチな情報を含む）"""
        return self.turn_manager.get_valid_actions_for_player(game, player_id)
    
    def _advance_to_next_street(self, game: GameState) -> None:
        """
        次のストリートに進み、ターンをリセットする
        責務: カード配布とターンセットアップのみ
        """
        # (注: ベット回収は process_action 側で実行済み)
        
        # コミュニティカードを配布
        # (deal_community_cards が game.current_round を更新する)
        self.dealer_service.deal_community_cards(game)
        
        # 新しいラウンドのターン状態をリセット
        self.turn_manager.reset_for_new_round(game)
        
        # 新しいラウンドの最初のアクター設定
        self.turn_manager.set_first_actor_for_round(game)
    
    def _check_and_run_it_out(self, game: GameState) -> bool:
        """
        アクション不要(active <= 1) かつ ショーダウン必要(in_hand > 1) の場合、
        リバーまで自動進行し、ショーダウンに進む。
        
        Returns:
            True: 処理成功
        """
        active_seats_count = len(game.table.active_seats())
        in_hand_seats_count = len(game.table.in_hand_seats())

        if active_seats_count <= 1 and in_hand_seats_count > 1:
            
            # リバーまで一気にカードを配る
            while game.current_round != Round.RIVER:
                # (ターンリセットやベット回収は不要なため、
                #  _advance_to_next_street ではなく deal_community_cards を直接呼ぶ)
                self.dealer_service.deal_community_cards(game)
            
            # ショーダウンへ
            self._proceed_to_showdown(game)
        
        return True
    
    def _proceed_to_fold_win(self, game: GameState) -> bool:
        """
        フォールド勝ちの処理
        
        Returns:
            True: 処理成功
        """
        # HandService.evaluate_showdown がフォールド勝ち(1人勝ち)にも対応している
        # ハンド評価を実行（1人だけが残っている場合でも評価される）
        self.hand_service.evaluate_hands_for_showdown(game)
        
        # ポット分配を実行
        winners_results = self.dealer_service.distribute_pots(game)
        game.winners = winners_results
        
        # ゲーム終了
        game.status = GameStatus.HAND_COMPLETE
        return True
    
    def _proceed_to_showdown(self, game: GameState) -> None:
        """ショーダウンに進む"""
        game.current_round = Round.SHOWDOWN

        # ハンドに参加している全プレイヤーのカードを公開
        in_hand_seats = [seat for seat in game.table.seats if seat.in_hand]
        for seat in in_hand_seats:
            seat.show_hand = True

        # 1. ハンド評価（HandService）
        self.hand_service.evaluate_hands_for_showdown(game)

        # 2. ポット分配（DealerService）
        winners_results = self.dealer_service.distribute_pots(game)
        game.winners = winners_results

        # ゲーム終了処理
        game.status = GameStatus.HAND_COMPLETE
    
    def _is_valid_action(self, game: GameState, action: PlayerAction) -> bool:
        """アクションが有効かチェック（TurnManagerのリッチな情報のみで判定）"""
        if game.status != GameStatus.IN_PROGRESS:
            return False

        # プレイヤーが存在するかチェック
        seat = game.table.get_seat_by_player_id(action.player_id)
        if not seat:
            return False

        # TurnManagerから有効なアクションリスト（リッチ情報）を取得
        valid_actions = self.turn_manager.get_valid_actions_for_player(game, action.player_id)
        for act in valid_actions:
            if act["type"] == action.action_type:
                # 金額指定が必要なアクションは範囲チェック
                if action.action_type in [ActionType.CALL]:
                    if "amount" in act:
                        # CALLの場合、正確な金額が必要
                        return action.amount == act["amount"] if hasattr(action, "amount") else False
                    else:
                        return True
                elif action.action_type in [ActionType.BET, ActionType.RAISE]:
                    if "min_amount" in act and "max_amount" in act:
                        # BET/RAISEの場合、範囲内であればOK
                        if hasattr(action, "amount"):
                            return act["min_amount"] <= action.amount <= act["max_amount"]
                        else:
                            return False
                    else:
                        return False
                else:
                    # FOLD, CHECKは金額不要
                    return True
        return False