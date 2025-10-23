import { useState } from 'react';
import HomePage from './pages/HomePage';
import LobbyPage from './pages/LobbyPage';
import GamePage from './pages/GamePage';
import './App.css';

type AppState = 'home' | 'lobby' | 'game';

function App() {
  const [currentPage, setCurrentPage] = useState<AppState>('home');
  const [username, setUsername] = useState('');

  const handleEnterLobby = (name: string) => {
    setUsername(name);
    setCurrentPage('lobby');
  };

  const handleStartSinglePlayer = () => {
    setCurrentPage('game');
  };

  const handleLogout = () => {
    setUsername('');
    setCurrentPage('home');
  };

  const handleExitGame = () => {
    setCurrentPage('lobby');
  };

  return (
    <>
      {currentPage === 'home' && (
        <HomePage onEnterLobby={handleEnterLobby} />
      )}
      {currentPage === 'lobby' && (
        <LobbyPage 
          username={username} 
          onStartSinglePlayer={handleStartSinglePlayer}
          onLogout={handleLogout}
        />
      )}
      {currentPage === 'game' && (
        <GamePage 
          username={username}
          onExitGame={handleExitGame}
        />
      )}
    </>
  );
}

export default App;
