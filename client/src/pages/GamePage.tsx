import { useState } from 'react';
import type { GameState, Player, Card } from '../types/game';
import './GamePage.css';

interface GamePageProps {
  username: string;
  onExitGame: () => void;
}

export default function GamePage({ username, onExitGame }: GamePageProps) {
  // TODO: WebSocketからのゲーム状態更新で_setGameStateを使用
  const [gameState, _setGameState] = useState<GameState>(initializeGame(username));
  const [betAmount, setBetAmount] = useState(40);

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
    // TODO: サーバーにアクションを送信
  };

  const handleExit = () => {
    if (confirm('ゲームを終了しますか？')) {
      onExitGame();
    }
  };

  const currentPlayer = gameState.players[gameState.currentPlayerIndex];
  const humanPlayer = gameState.players.find(p => !p.isAI);

  return (
    <div className="game-page">
      {/* ヘッダー */}
      <div className="game-header">
        <div className="game-info">
          <div className="info-item">
            <span className="info-label">ブラインド</span>
            <span className="info-value">${gameState.smallBlind}/${gameState.bigBlind}</span>
          </div>
          <div className="info-item">
            <span className="info-label">フェーズ</span>
            <span className="info-value">{getPhaseText(gameState.phase)}</span>
          </div>
          <div className="info-item">
            <span className="info-label">あなたのチップ</span>
            <span className="info-value chips">${humanPlayer?.chips || 0}</span>
          </div>
        </div>
        <button className="exit-button" onClick={handleExit}>
          退出
        </button>
      </div>

      {/* ゲームエリア */}
      <div className="game-area">
        <div className="poker-table">
          <div className="table-felt">
            {/* ポット */}
            <div className="pot-area">
              <div className="pot-label">ポット</div>
              <div className="pot-amount">${gameState.pot}</div>
            </div>

            {/* コミュニティカード */}
            <div className="community-cards">
              {[0, 1, 2, 3, 4].map((index) => (
                <div key={index} className="card-slot">
                  {gameState.communityCards[index] ? (
                    <PlayingCard card={gameState.communityCards[index]} />
                  ) : (
                    <div className="card empty"></div>
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
      <div className="action-panel">
        <div className="action-buttons">
          <button className="action-btn fold" onClick={() => handleAction('fold')}>
            フォールド
          </button>
          <button className="action-btn check" onClick={() => handleAction('check')}>
            チェック
          </button>
          <button className="action-btn call" onClick={() => handleAction('call')}>
            コール ($20)
          </button>
          <button className="action-btn raise" onClick={() => handleAction('raise')}>
            レイズ
          </button>
          <button className="action-btn all-in" onClick={() => handleAction('allin')}>
            オールイン
          </button>
        </div>
        
        <div className="bet-controls">
          <input
            type="range"
            min={gameState.bigBlind}
            max={humanPlayer?.chips || 1000}
            value={betAmount}
            onChange={(e) => setBetAmount(Number(e.target.value))}
            className="bet-slider"
          />
          <div className="bet-amount">${betAmount}</div>
        </div>
      </div>
    </div>
  );
}

// プレイヤー席コンポーネント
function PlayerSeat({ player, isActive, isHuman }: { player: Player; isActive: boolean; isHuman: boolean }) {
  return (
    <div className={`player-seat seat-${player.position} ${isActive ? 'active' : ''} ${player.hasFolded ? 'folded' : ''}`}>
      <div className="player-info">
        {player.isDealer && <div className="dealer-button">D</div>}
        <div className="player-name">{player.name}</div>
        <div className="player-chips">${player.chips}</div>
        {player.bet > 0 && <div className="player-bet">${player.bet}</div>}
      </div>
      
      {player.cards.length > 0 && (
        <div className="player-cards">
          {player.cards.map((card, index) => (
            <div key={index} className="card-wrapper">
              {isHuman ? (
                <PlayingCard card={card} />
              ) : (
                <div className="card back"></div>
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
    <div className={`card ${isRed ? 'red' : 'black'}`}>
      <div className="card-corner top-left">
        <div className="rank">{card.rank}</div>
        <div className="suit">{suitSymbols[card.suit]}</div>
      </div>
      <div className="card-center">
        {suitSymbols[card.suit]}
      </div>
      <div className="card-corner bottom-right">
        <div className="rank">{card.rank}</div>
        <div className="suit">{suitSymbols[card.suit]}</div>
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
