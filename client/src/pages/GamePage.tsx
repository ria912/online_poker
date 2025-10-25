import { useMemo, useState } from 'react';
import type { GameState, Player, Card } from '../types/game';
import { useGameWebSocket } from '../hooks/useGameWebSocket';

interface GamePageProps {
  username: string;
  onExitGame: () => void;
}

export default function GamePage({ username, onExitGame }: GamePageProps) {
  // TODO: WebSocketからのゲーム状態更新で_setGameStateを使用
  const [gameState, setGameState] = useState<GameState>(initializeGame(username));
  const [betAmount, setBetAmount] = useState(40);

  // WebSocket接続
  const { sendAction, sendChat: _sendChat, isConnected } = useGameWebSocket({
    gameId: 'single-player-1', // シングルプレイ用のゲームID
    username,
    onGameStateUpdate: (state) => {
      console.log('Game state updated:', state);
      setGameState(state);
    },
    onPlayerAction: (data) => {
      console.log('Player action:', data);
    },
    onChatMessage: (user, message) => {
      console.log(`Chat from ${user}: ${message}`);
    },
    onSystemMessage: (message) => {
      console.log('System message:', message);
    },
  });

  // 初期ゲーム状態を作成
  function initializeGame(playerName: string): GameState {
    const players: Player[] = [
      {
        id: '1',
        name: playerName,
        chips: 1000,
        bet: 0,
        cards: [],
        isDealer: true,
        isActive: true,
        hasFolded: false,
        isAI: false,
        position: 0,
      },
      {
        id: '2',
        name: 'AI Player 1',
        chips: 1000,
        bet: 0,
        cards: [],
        isDealer: false,
        isActive: false,
        hasFolded: false,
        isAI: true,
        position: 1,
      },
      {
        id: '3',
        name: 'AI Player 2',
        chips: 1000,
        bet: 0,
        cards: [],
        isDealer: false,
        isActive: false,
        hasFolded: false,
        isAI: true,
        position: 2,
      },
    ];

    return {
      players,
      communityCards: [],
      pot: 0,
      currentPlayerIndex: 0,
      phase: 'waiting',
      dealerIndex: 0,
      smallBlind: 10,
      bigBlind: 20,
    };
  }

  const handleAction = (action: string) => {
    console.log('Action:', action);
    
    // WebSocketでサーバーにアクションを送信
    if (action === 'raise') {
      sendAction(action, betAmount);
    } else {
      sendAction(action);
    }
  };

  const handleExit = () => {
    if (confirm('ゲームを終了しますか？')) {
      onExitGame();
    }
  };

  const currentPlayer = gameState.players[gameState.currentPlayerIndex];
  const humanPlayer = gameState.players.find(p => !p.isAI);

  return (
    <div className="h-screen flex flex-col bg-[linear-gradient(135deg,#0f2027_0%,#203a43_50%,#2c5364_100%)] text-white overflow-hidden">
      {/* ヘッダー */}
      <div className="bg-black/50 px-6 py-4 flex items-center justify-between border-b border-white/10">
        <div className="flex gap-10">
          <div className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-wide text-white/60">接続状態</span>
            <span className={`text-lg font-bold ${isConnected ? 'text-green-500' : 'text-red-500'}`}>
              {isConnected ? '🟢 接続中' : '🔴 切断'}
            </span>
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-wide text-white/60">ブラインド</span>
            <span className="text-lg font-bold">${gameState.smallBlind}/${gameState.bigBlind}</span>
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-wide text-white/60">フェーズ</span>
            <span className="text-lg font-bold">{getPhaseText(gameState.phase)}</span>
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-wide text-white/60">あなたのチップ</span>
            <span className="text-lg font-bold text-yellow-400">${humanPlayer?.chips || 0}</span>
          </div>
        </div>
        <button className="px-6 py-2 rounded-md bg-red-600/80 hover:bg-red-600 transition font-bold text-sm" onClick={handleExit}>
          退出
        </button>
      </div>

      {/* ゲームエリア */}
      <div className="flex-1 flex items-center justify-center p-5 relative">
        <div className="w-full max-w-[1000px] h-full max-h-[600px] flex items-center justify-center">
          <div className="relative w-full h-full rounded-full border-[15px] border-[#8b4513] shadow-[0_10px_50px_rgba(0,0,0,0.5),_inset_0_0_50px_rgba(0,0,0,0.3)] flex items-center justify-center bg-[linear-gradient(135deg,#1a5f3f_0%,#0d4028_100%)]">
            {/* ポット */}
            <div className="absolute left-1/2 top-[25%] -translate-x-1/2 -translate-y-1/2 bg-black/70 px-10 py-5 rounded-2xl border-3 border-yellow-300 shadow-[0_0_20px_rgba(255,215,0,0.3)] text-center z-10">
              <div className="text-sm text-white/80 uppercase tracking-wide mb-1">ポット</div>
              <div className="text-3xl font-bold text-yellow-300 drop-shadow">${gameState.pot}</div>
            </div>

            {/* コミュニティカード */}
            <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 flex gap-3">
              {[0, 1, 2, 3, 4].map((index) => (
                <div key={index} className="w-[70px] h-[98px]">
                  {gameState.communityCards[index] ? (
                    <PlayingCard card={gameState.communityCards[index]} />
                  ) : (
                    <div className="w-[70px] h-[98px] rounded-lg border-2 border-dashed border-white/30 bg-white/10" />
                  )}
                </div>
              ))}
            </div>

            {/* プレイヤー */}
            {gameState.players.map((player) => (
              <PlayerSeat
                key={player.id}
                player={player}
                isActive={player.id === currentPlayer.id}
                isHuman={!player.isAI}
              />
            ))}
          </div>
        </div>
      </div>

      {/* アクションパネル */}
      <div className="bg-black/80 backdrop-blur px-6 py-6 border-t border-white/10 flex flex-col md:flex-row items-center justify-center gap-6">
        <div className="flex gap-3 flex-wrap justify-center">
          <button className="min-w-[110px] px-6 py-3 rounded-lg font-bold text-white uppercase tracking-wide transition hover:-translate-y-0.5 shadow bg-[linear-gradient(135deg,#dc3545_0%,#c82333_100%)]" onClick={() => handleAction('fold')}>
            フォールド
          </button>
          <button className="min-w-[110px] px-6 py-3 rounded-lg font-bold text-white uppercase tracking-wide transition hover:-translate-y-0.5 shadow bg-[linear-gradient(135deg,#6c757d_0%,#5a6268_100%)]" onClick={() => handleAction('check')}>
            チェック
          </button>
          <button className="min-w-[110px] px-6 py-3 rounded-lg font-bold text-white uppercase tracking-wide transition hover:-translate-y-0.5 shadow bg-[linear-gradient(135deg,#17a2b8_0%,#138496_100%)]" onClick={() => handleAction('call')}>
            コール (${gameState.bigBlind})
          </button>
          <button className="min-w-[110px] px-6 py-3 rounded-lg font-bold text-white uppercase tracking-wide transition hover:-translate-y-0.5 shadow bg-[linear-gradient(135deg,#28a745_0%,#218838_100%)]" onClick={() => handleAction('raise')}>
            レイズ
          </button>
          <button className="min-w-[110px] px-6 py-3 rounded-lg font-bold text-black uppercase tracking-wide transition hover:-translate-y-0.5 shadow text-base bg-[linear-gradient(135deg,#ffd700_0%,#ff8c00_100%)]" onClick={() => handleAction('allin')}>
            オールイン
          </button>
        </div>

        <div className="flex items-center gap-4">
          <input
            type="range"
            min={gameState.bigBlind}
            max={humanPlayer?.chips || 1000}
            value={betAmount}
            onChange={(e) => setBetAmount(Number(e.target.value))}
            className="w-[200px] h-1.5 rounded-full bg-white/20 cursor-pointer"
            style={{ accentColor: '#facc15' }}
          />
          <div className="text-xl font-bold text-yellow-400 min-w-[100px] text-center bg-yellow-400/10 px-4 py-2 rounded-lg border-2 border-yellow-400/30">
            ${betAmount}
          </div>
        </div>
      </div>
    </div>
  );
}

// プレイヤー席コンポーネント
function PlayerSeat({ player, isActive, isHuman }: { player: Player; isActive: boolean; isHuman: boolean }) {
  const seatClass = useMemo(() => {
    if (player.position === 0) return 'bottom-[-80px] left-1/2 -translate-x-1/2';
    if (player.position === 1) return 'top-1/2 left-[-80px] -translate-y-1/2';
    return 'top-1/2 right-[-80px] -translate-y-1/2';
  }, [player.position]);

  return (
    <div className={`absolute z-20 flex flex-col items-center gap-2 ${seatClass} ${player.hasFolded ? 'opacity-50' : ''}`}>
      <div className={`relative min-w-[140px] text-center px-5 py-4 rounded-xl border-2 backdrop-blur bg-black/85 transition ${isActive ? 'border-yellow-400 shadow-[0_0_25px_rgba(255,215,0,0.5)] animate-pulse' : 'border-white/20'}`}>
        {player.isDealer && (
          <div className="absolute -top-3 -right-3 w-8 h-8 rounded-full bg-white border-3 border-black text-black font-bold flex items-center justify-center shadow">
            D
          </div>
        )}
        <div className="text-white font-bold mb-1 text-sm">{player.name}</div>
        <div className="text-yellow-400 font-bold text-base">${player.chips}</div>
        {player.bet > 0 && (
          <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-yellow-300/90 text-black px-3 py-1 rounded-xl text-sm font-bold shadow">
            ${player.bet}
          </div>
        )}
      </div>

      {player.cards.length > 0 && (
        <div className="flex gap-2">
          {player.cards.map((card, index) => (
            <div key={index} className="scale-80">
              {isHuman ? (
                <PlayingCard card={card} />
              ) : (
                <div className="w-[70px] h-[98px] rounded-lg flex items-center justify-center text-5xl text-white bg-[linear-gradient(135deg,#0066cc_0%,#004499_100%)]">🂠</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// カードコンポーネント
function PlayingCard({ card }: { card: Card }) {
  const suitSymbols = {
    hearts: '♥',
    diamonds: '♦',
    clubs: '♣',
    spades: '♠',
  };

  const isRed = card.suit === 'hearts' || card.suit === 'diamonds';

  return (
    <div className={`relative w-[70px] h-[98px] rounded-lg bg-white shadow-[0_4px_12px_rgba(0,0,0,0.4)] hover:-translate-y-1 hover:shadow-[0_8px_20px_rgba(0,0,0,0.5)] transition text-${isRed ? 'red-600' : 'black'}`}>
      <div className="absolute top-0 left-0 p-1.5 flex flex-col items-center leading-none">
        <div className="text-sm font-bold">{card.rank}</div>
        <div className="text-xs">{suitSymbols[card.suit]}</div>
      </div>
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-4xl">
        {suitSymbols[card.suit]}
      </div>
      <div className="absolute bottom-0 right-0 p-1.5 flex flex-col items-center leading-none rotate-180">
        <div className="text-sm font-bold">{card.rank}</div>
        <div className="text-xs">{suitSymbols[card.suit]}</div>
      </div>
    </div>
  );
}

function getPhaseText(phase: string): string {
  const phaseMap: { [key: string]: string } = {
    waiting: '待機中',
    preflop: 'プリフロップ',
    flop: 'フロップ',
    turn: 'ターン',
    river: 'リバー',
    showdown: 'ショーダウン',
  };
  return phaseMap[phase] || phase;
}
