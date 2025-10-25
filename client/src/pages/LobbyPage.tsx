import { useState } from 'react';

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
    <div className="min-h-screen text-white bg-[linear-gradient(135deg,#0f2027_0%,#203a43_50%,#2c5364_100%)]">
      <div className="bg-black/30 backdrop-blur p-5 md:px-10 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-white/10">
        <div>
          <h1 className="text-2xl md:text-3xl">♠️ ロビー ♥️</h1>
        </div>
        <div className="flex items-center gap-5">
          <span className="text-sm">ようこそ、<strong className="text-sky-400">{username}</strong>さん</span>
          <button onClick={onLogout} className="px-4 py-2 rounded-md bg-red-600/80 hover:bg-red-600 transition font-bold text-sm">
            退室
          </button>
        </div>
      </div>

      <div className="max-w-[1400px] mx-auto p-5 md:p-10">
        <div>
          <section className="mb-12">
            <h2 className="text-2xl mb-6 border-l-4 border-sky-400 pl-5">ゲームモード</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {/* シングルプレイ */}
              <div className="bg-white/5 backdrop-blur border-2 border-sky-400 rounded-2xl overflow-hidden shadow-[0_0_30px_rgba(77,184,255,0.2)]">
                <div className="p-8 text-center relative">
                  <div className="text-6xl mb-4">🎮</div>
                  <h3 className="text-2xl mb-2">シングルプレイ</h3>
                  <span className="absolute right-6 top-6 inline-block px-2 py-1 rounded-md text-[10px] font-bold uppercase text-white bg-[linear-gradient(135deg,#f093fb_0%,#f5576c_100%)]">
                    おすすめ
                  </span>
                </div>
                <div className="px-8 pb-8">
                  <p className="text-white/80 mb-6 leading-relaxed">
                    AIと対戦してポーカーの腕を磨こう！
                  </p>
                  <div className="flex flex-col gap-3">
                    <div className="flex justify-between px-3 py-2 bg-white/5 rounded-md">
                      <span className="text-white/70 text-sm">プレイヤー:</span>
                      <span className="font-bold text-sm">1人 + AI 2人</span>
                    </div>
                    <div className="flex justify-between px-3 py-2 bg-white/5 rounded-md">
                      <span className="text-white/70 text-sm">開始チップ:</span>
                      <span className="font-bold text-sm">$1,000</span>
                    </div>
                    <div className="flex justify-between px-3 py-2 bg-white/5 rounded-md">
                      <span className="text-white/70 text-sm">ブラインド:</span>
                      <span className="font-bold text-sm">$10 / $20</span>
                    </div>
                  </div>
                </div>
                <div className="px-8 pb-8">
                  <button
                    onClick={handleStartSinglePlayer}
                    className="w-full py-4 text-lg font-bold rounded-xl text-white transition hover:scale-[1.02] shadow bg-[linear-gradient(135deg,#4db8ff_0%,#2a5298_100%)] disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={isLoading}
                  >
                    {isLoading ? 'ゲーム準備中...' : 'ゲーム開始'}
                  </button>
                </div>
              </div>

              {/* マルチプレイ */}
              <div className="bg-white/5 backdrop-blur border-2 border-white/10 rounded-2xl overflow-hidden opacity-60 cursor-not-allowed">
                <div className="p-8 text-center relative">
                  <div className="text-6xl mb-4">👥</div>
                  <h3 className="text-2xl mb-2">マルチプレイ</h3>
                  <span className="absolute right-6 top-6 inline-block px-2 py-1 rounded-md text-[10px] font-bold uppercase text-white bg-white/20">
                    準備中
                  </span>
                </div>
                <div className="px-8 pb-8">
                  <p className="text-white/80 mb-6 leading-relaxed">友達とオンラインで対戦しよう！</p>
                  <div className="flex flex-col gap-3">
                    <div className="flex justify-between px-3 py-2 bg-white/5 rounded-md">
                      <span className="text-white/70 text-sm">プレイヤー:</span>
                      <span className="font-bold text-sm">2-6人</span>
                    </div>
                    <div className="flex justify-between px-3 py-2 bg-white/5 rounded-md">
                      <span className="text-white/70 text-sm">ルーム作成:</span>
                      <span className="font-bold text-sm">カスタム設定可能</span>
                    </div>
                  </div>
                </div>
                <div className="px-8 pb-8">
                  <button className="w-full py-4 text-lg font-bold rounded-xl bg-white/20 text-white" disabled>
                    近日公開
                  </button>
                </div>
              </div>

              {/* トーナメント */}
              <div className="bg-white/5 backdrop-blur border-2 border-white/10 rounded-2xl overflow-hidden opacity-60 cursor-not-allowed">
                <div className="p-8 text-center relative">
                  <div className="text-6xl mb-4">🏆</div>
                  <h3 className="text-2xl mb-2">トーナメント</h3>
                  <span className="absolute right-6 top-6 inline-block px-2 py-1 rounded-md text-[10px] font-bold uppercase text-white bg-white/20">
                    準備中
                  </span>
                </div>
                <div className="px-8 pb-8">
                  <p className="text-white/80 mb-6 leading-relaxed">大会形式で競い合おう！</p>
                  <div className="flex flex-col gap-3">
                    <div className="flex justify-between px-3 py-2 bg-white/5 rounded-md">
                      <span className="text-white/70 text-sm">プレイヤー:</span>
                      <span className="font-bold text-sm">8-16人</span>
                    </div>
                    <div className="flex justify-between px-3 py-2 bg-white/5 rounded-md">
                      <span className="text-white/70 text-sm">形式:</span>
                      <span className="font-bold text-sm">シングルエリミネーション</span>
                    </div>
                  </div>
                </div>
                <div className="px-8 pb-8">
                  <button className="w-full py-4 text-lg font-bold rounded-xl bg-white/20 text-white" disabled>
                    近日公開
                  </button>
                </div>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-2xl mb-6 border-l-4 border-sky-400 pl-5">統計情報</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
              <div className="text-center bg-white/5 backdrop-blur border border-white/10 rounded-xl p-6 transition hover:-translate-y-1 hover:bg-white/10">
                <div className="text-4xl mb-2">🎯</div>
                <div className="text-2xl font-bold text-sky-400 mb-1">0</div>
                <div className="text-xs uppercase tracking-wide text-white/70">総ゲーム数</div>
              </div>
              <div className="text-center bg-white/5 backdrop-blur border border-white/10 rounded-xl p-6 transition hover:-translate-y-1 hover:bg-white/10">
                <div className="text-4xl mb-2">🏅</div>
                <div className="text-2xl font-bold text-sky-400 mb-1">0%</div>
                <div className="text-xs uppercase tracking-wide text-white/70">勝率</div>
              </div>
              <div className="text-center bg-white/5 backdrop-blur border border-white/10 rounded-xl p-6 transition hover:-translate-y-1 hover:bg-white/10">
                <div className="text-4xl mb-2">💰</div>
                <div className="text-2xl font-bold text-sky-400 mb-1">$0</div>
                <div className="text-xs uppercase tracking-wide text-white/70">総獲得額</div>
              </div>
              <div className="text-center bg-white/5 backdrop-blur border border-white/10 rounded-xl p-6 transition hover:-translate-y-1 hover:bg-white/10">
                <div className="text-4xl mb-2">⭐</div>
                <div className="text-2xl font-bold text-sky-400 mb-1">初心者</div>
                <div className="text-xs uppercase tracking-wide text-white/70">ランク</div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
