from typing import Optional, List
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
        self.turn_manager.start_round(game)
        
        return True

    async def process_action(self, game: GameState, action: PlayerAction) -> bool:
        """プレイヤーアクションを処理"""
        if not self._is_valid_action(game, action):
            return False
        
        # アクションを実行
        success = await self.action_service.execute_action(game, action)
        if not success:
            return False
        
        # アクション履歴に追加
        game.history.append(action)
        
        # 次のアクターに進む
        round_continues = self.turn_manager.advance_turn(game)
        
        # ベッティングラウンド終了チェック
        if not round_continues:
            self._advance_to_next_round(game)
        
        return True
    
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
    
    def get_valid_actions(self, game: GameState, player_id: str) -> List[ActionType]:
        """プレイヤーの有効なアクションを取得"""
        # プレイヤーIDから座席を探す
        seat = self._find_player_seat(game, player_id)
        if not seat:
            return []
        
        return self.turn_manager.get_valid_actions(game, seat.index)
    
    def _advance_to_next_round(self, game: GameState) -> None:
        """次のベッティングラウンドに進む"""
        # ベットをポットに回収
        self.dealer_service.collect_bets_to_pots(game)
        
        # 次のラウンドに進む
        if game.current_round == Round.PREFLOP:
            game.current_round = Round.FLOP
            self.dealer_service.deal_community_cards(game, Round.PREFLOP)
        elif game.current_round == Round.FLOP:
            game.current_round = Round.TURN
            self.dealer_service.deal_community_cards(game, Round.FLOP)
        elif game.current_round == Round.TURN:
            game.current_round = Round.RIVER
            self.dealer_service.deal_community_cards(game, Round.TURN)
        elif game.current_round == Round.RIVER:
            self._proceed_to_showdown(game)
            return
        
        # 新しいラウンドの最初のアクター設定
        self.turn_manager.start_round(game)
    
    def _proceed_to_showdown(self, game: GameState) -> None:
        """ショーダウンに進む"""
        game.current_round = Round.SHOWDOWN
        
        # ハンドに参加している全プレイヤーのカードを公開
        in_hand_seats = [seat for seat in game.table.seats if seat.in_hand]
        for seat in in_hand_seats:
            seat.show_hand = True
        
        # ハンド評価とポット分配
        winners = self.hand_service.evaluate_showdown(game)
        game.winners = winners
        
        # ゲーム終了処理
        game.status = GameStatus.HAND_COMPLETE
    
    def _is_valid_action(self, game: GameState, action: PlayerAction) -> bool:
        """アクションが有効かチェック"""
        # 基本的な検証
        if game.status != GameStatus.IN_PROGRESS:
            return False
        
        # プレイヤーが存在するかチェック
        seat = self._find_player_seat(game, action.player_id)
        if not seat:
            return False
        
        # ターンマネージャーで有効なアクションかチェック
        valid_actions = self.turn_manager.get_valid_actions(game, seat.index)
        if action.action_type not in valid_actions:
            return False
        
        # アクションサービスに詳細検証を委譲
        return self.action_service.is_valid_action(game, action)
    
    def _find_player_seat(self, game: GameState, player_id: str) -> Optional[Seat]:
        """プレイヤーIDから座席を検索"""
        for seat in game.table.seats:
            if seat.is_occupied and seat.player.id == player_id:
                return seat
        return None