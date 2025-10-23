/**
 * ゲーム関連の型定義
 */

export interface Player {
  id: string;
  name: string;
  chips: number;
  bet: number;
  cards: Card[];
  isDealer: boolean;
  isActive: boolean;
  hasFolded: boolean;
  isAI: boolean;
  position: number;
}

export interface Card {
  suit: 'hearts' | 'diamonds' | 'clubs' | 'spades';
  rank: string;
}

export interface GameState {
  players: Player[];
  communityCards: Card[];
  pot: number;
  currentPlayerIndex: number;
  phase: 'waiting' | 'preflop' | 'flop' | 'turn' | 'river' | 'showdown';
  dealerIndex: number;
  smallBlind: number;
  bigBlind: number;
}

export interface WebSocketMessage {
  type: 'game_state' | 'player_action' | 'chat' | 'system' | 'message' | 'user_joined' | 'user_left' | 'room_info';
  [key: string]: any;
}
