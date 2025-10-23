/**
 * ゲーム用WebSocket接続フック
 */
import { useCallback } from 'react';
import { useWebSocket } from './useWebSocket';
import type { WebSocketMessage, GameState } from '../types/game';

interface UseGameWebSocketOptions {
  gameId: string;
  username: string;
  onGameStateUpdate?: (state: GameState) => void;
  onPlayerAction?: (data: any) => void;
  onChatMessage?: (username: string, message: string) => void;
  onSystemMessage?: (message: string) => void;
}

export function useGameWebSocket(options: UseGameWebSocketOptions) {
  const { gameId, username, onGameStateUpdate, onPlayerAction, onChatMessage, onSystemMessage } = options;

  // WebSocketのURL構築
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/game/${gameId}?username=${encodeURIComponent(username)}`;

  const handleMessage = useCallback((data: WebSocketMessage) => {
    console.log('Received message:', data);

    switch (data.type) {
      case 'connected':
        console.log('Connected to game:', data.game_id);
        break;

      case 'game_state':
        if (data.state && onGameStateUpdate) {
          onGameStateUpdate(data.state);
        }
        break;

      case 'player_action':
        if (onPlayerAction) {
          onPlayerAction(data);
        }
        break;

      case 'chat':
        if (onChatMessage && data.username && data.message) {
          onChatMessage(data.username, data.message);
        }
        break;

      case 'player_joined':
      case 'player_left':
      case 'system':
        if (onSystemMessage && data.message) {
          onSystemMessage(data.message);
        }
        break;

      default:
        console.log('Unknown message type:', data.type);
    }
  }, [onGameStateUpdate, onPlayerAction, onChatMessage, onSystemMessage]);

  const { sendMessage, disconnect, isConnected } = useWebSocket(wsUrl, {
    onMessage: handleMessage,
    onOpen: () => {
      console.log('Game WebSocket opened');
    },
    onClose: () => {
      console.log('Game WebSocket closed');
    },
    onError: (error) => {
      console.error('Game WebSocket error:', error);
    },
  });

  // アクション送信
  const sendAction = useCallback((action: string, amount?: number) => {
    sendMessage({
      type: 'action',
      action,
      amount: amount || 0,
    });
  }, [sendMessage]);

  // チャット送信
  const sendChat = useCallback((message: string) => {
    sendMessage({
      type: 'chat',
      message,
    });
  }, [sendMessage]);

  // ゲーム状態リクエスト
  const requestGameState = useCallback(() => {
    sendMessage({
      type: 'get_state',
    });
  }, [sendMessage]);

  return {
    sendAction,
    sendChat,
    requestGameState,
    disconnect,
    isConnected,
  };
}
