import { useState } from 'react';
import './LobbyPage.css';

interface LobbyPageProps {
  username: string;
  onStartSinglePlayer: () => void;
  onLogout: () => void;
}

export default function LobbyPage({ username, onStartSinglePlayer, onLogout }: LobbyPageProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleStartSinglePlayer = () => {
    setIsLoading(true);
    // 少し遅延を入れてローディング効果を出す
    setTimeout(() => {
      onStartSinglePlayer();
    }, 500);
  };

  return (
    <div className="lobby-page">
      <div className="lobby-header">
        <div className="lobby-title">
          <h1>♠️ ロビー ♥️</h1>
        </div>
        <div className="user-section">
          <span className="welcome-text">ようこそ、<strong>{username}</strong>さん</span>
          <button onClick={onLogout} className="logout-button">退室</button>
        </div>
      </div>

      <div className="lobby-container">
        <div className="lobby-content">
          <section className="game-modes">
            <h2>ゲームモード</h2>
            
            <div className="game-mode-cards">
              <div className="game-mode-card featured">
                <div className="card-header">
                  <div className="mode-icon">🎮</div>
                  <h3>シングルプレイ</h3>
                  <span className="badge recommended">おすすめ</span>
                </div>
                <div className="card-body">
                  <p className="mode-description">
                    AIと対戦してポーカーの腕を磨こう！
                  </p>
                  <div className="mode-details">
                    <div className="detail-item">
                      <span className="detail-label">プレイヤー:</span>
                      <span className="detail-value">1人 + AI 2人</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">開始チップ:</span>
                      <span className="detail-value">$1,000</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">ブラインド:</span>
                      <span className="detail-value">$10 / $20</span>
                    </div>
                  </div>
                </div>
                <div className="card-footer">
                  <button 
                    onClick={handleStartSinglePlayer} 
                    className="start-button"
                    disabled={isLoading}
                  >
                    {isLoading ? 'ゲーム準備中...' : 'ゲーム開始'}
                  </button>
                </div>
              </div>

              <div className="game-mode-card disabled">
                <div className="card-header">
                  <div className="mode-icon">👥</div>
                  <h3>マルチプレイ</h3>
                  <span className="badge coming-soon">準備中</span>
                </div>
                <div className="card-body">
                  <p className="mode-description">
                    友達とオンラインで対戦しよう！
                  </p>
                  <div className="mode-details">
                    <div className="detail-item">
                      <span className="detail-label">プレイヤー:</span>
                      <span className="detail-value">2-6人</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">ルーム作成:</span>
                      <span className="detail-value">カスタム設定可能</span>
                    </div>
                  </div>
                </div>
                <div className="card-footer">
                  <button className="start-button" disabled>
                    近日公開
                  </button>
                </div>
              </div>

              <div className="game-mode-card disabled">
                <div className="card-header">
                  <div className="mode-icon">🏆</div>
                  <h3>トーナメント</h3>
                  <span className="badge coming-soon">準備中</span>
                </div>
                <div className="card-body">
                  <p className="mode-description">
                    大会形式で競い合おう！
                  </p>
                  <div className="mode-details">
                    <div className="detail-item">
                      <span className="detail-label">プレイヤー:</span>
                      <span className="detail-value">8-16人</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">形式:</span>
                      <span className="detail-value">シングルエリミネーション</span>
                    </div>
                  </div>
                </div>
                <div className="card-footer">
                  <button className="start-button" disabled>
                    近日公開
                  </button>
                </div>
              </div>
            </div>
          </section>

          <section className="quick-stats">
            <h2>統計情報</h2>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon">🎯</div>
                <div className="stat-value">0</div>
                <div className="stat-label">総ゲーム数</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">🏅</div>
                <div className="stat-value">0%</div>
                <div className="stat-label">勝率</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">💰</div>
                <div className="stat-value">$0</div>
                <div className="stat-label">総獲得額</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">⭐</div>
                <div className="stat-value">初心者</div>
                <div className="stat-label">ランク</div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
