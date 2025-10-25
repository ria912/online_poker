import { useState } from 'react';

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
    <div className="min-h-screen bg-[linear-gradient(135deg,#1e3c72_0%,#2a5298_100%)] flex items-center justify-center p-5">
      <div className="w-full max-w-[1200px]">
        <div className="text-center mb-16">
          <h1 className="text-white drop-shadow-md text-4xl md:text-5xl mb-2">♠️ オンラインポーカー ♥️</h1>
          <p className="text-white/90 text-lg font-light">テキサスホールデム</p>
          <span className="mt-3 inline-block rounded-full bg-indigo-600 px-3 py-1 text-xs font-medium text-white shadow-sm">
            Tailwind 有効
          </span>
        </div>

        <div className="flex flex-col gap-10">
          <div className="bg-white rounded-2xl p-10 md:p-14 shadow-2xl text-center">
            <h2 className="text-2xl md:text-3xl text-gray-800 mb-8">ようこそ</h2>
            <form onSubmit={handleSubmit} className="flex flex-col gap-5 max-w-[400px] mx-auto">
              <input
                type="text"
                placeholder="名前を入力してください"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                maxLength={20}
                className="px-6 py-4 text-lg border-2 border-gray-200 rounded-xl transition focus:outline-none focus:border-[#2a5298] focus:ring-3 focus:ring-[#2a5298]/10"
                autoFocus
              />
              <button
                type="submit"
                className="px-6 py-4 text-lg font-bold text-white rounded-xl transition shadow bg-[linear-gradient(135deg,#1e3c72_0%,#2a5298_100%)] hover:-translate-y-0.5 hover:shadow-2xl disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={!username.trim()}
              >
                入室する
              </button>
            </form>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-7">
            <div className="text-white text-center bg-white/10 backdrop-blur border border-white/20 rounded-2xl p-10 transition hover:-translate-y-1 hover:bg-white/15 hover:shadow-2xl">
              <div className="text-5xl mb-5">🎮</div>
              <h3 className="text-xl md:text-2xl mb-3">シングルプレイ</h3>
              <p className="text-base opacity-90 leading-relaxed">AIと対戦してポーカーを楽しもう</p>
            </div>
            <div className="text-white text-center bg-white/10 backdrop-blur border border-white/20 rounded-2xl p-10 transition hover:-translate-y-1 hover:bg-white/15 hover:shadow-2xl">
              <div className="text-5xl mb-5">👥</div>
              <h3 className="text-xl md:text-2xl mb-3">マルチプレイ</h3>
              <p className="text-base opacity-90 leading-relaxed">友達とオンラインで対戦</p>
            </div>
            <div className="text-white text-center bg-white/10 backdrop-blur border border-white/20 rounded-2xl p-10 transition hover:-translate-y-1 hover:bg-white/15 hover:shadow-2xl">
              <div className="text-5xl mb-5">📊</div>
              <h3 className="text-xl md:text-2xl mb-3">戦績記録</h3>
              <p className="text-base opacity-90 leading-relaxed">勝率や統計を記録</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
