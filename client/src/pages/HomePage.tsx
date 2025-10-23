import { useState } from 'react';
import './HomePage.css';

interface HomePageProps {
  onEnterLobby: (username: string) => void;
}

export default function HomePage({ onEnterLobby }: HomePageProps) {
  const [username, setUsername] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedUsername = username.trim();
    if (trimmedUsername) {
      onEnterLobby(trimmedUsername);
    }
  };

  return (
    <div className="home-page">
      <div className="home-container">
        <div className="home-header">
          <h1>♠️ オンラインポーカー ♥️</h1>
          <p className="subtitle">テキサスホールデム</p>
        </div>
        
        <div className="home-content">
          <div className="welcome-card">
            <h2>ようこそ</h2>
            <form onSubmit={handleSubmit} className="login-form">
              <input
                type="text"
                placeholder="名前を入力してください"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                maxLength={20}
                className="username-input"
                autoFocus
              />
              <button type="submit" className="enter-button" disabled={!username.trim()}>
                入室する
              </button>
            </form>
          </div>

          <div className="features">
            <div className="feature-card">
              <div className="feature-icon">🎮</div>
              <h3>シングルプレイ</h3>
              <p>AIと対戦してポーカーを楽しもう</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">👥</div>
              <h3>マルチプレイ</h3>
              <p>友達とオンラインで対戦</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h3>戦績記録</h3>
              <p>勝率や統計を記録</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
