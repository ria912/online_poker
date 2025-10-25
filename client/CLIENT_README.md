# Online Poker - Client

React + TypeScript + Vite で構築されたオンラインポーカーのフロントエンドクライアント

## 🎮 アプリケーション構成

### ページフロー

```
ホームページ (名前入力)
    ↓
ロビーページ (ゲームモード選択)
    ↓
ゲームページ (ポーカーゲーム)
```

### 主要コンポーネント

- **HomePage** - 名前入力画面
- **LobbyPage** - ゲームモード選択（シングルプレイ: 人間1人 + AI 2人）
- **GamePage** - ポーカーゲーム画面

## 🚀 セットアップ

```bash
# インストール
npm install

# 開発サーバー起動
npm run dev

# 本番ビルド
npm run build
```

## 🎨 スタイリング（Tailwind CSS v4）

このプロジェクトは Tailwind CSS v4 を Vite プラグインで利用しています。

- 参照設定: `vite.config.ts` に `@tailwindcss/vite` を追加
- 読み込み: `src/index.css` の先頭で `@import "tailwindcss";`

すぐにユーティリティクラスが使えます（例）:

```tsx
<button className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">
    送信
</button>
```

既存の CSS ファイル（例: `HomePage.css` など）はそのまま併用できます。必要に応じて段階的にユーティリティへ移行してください。

## 📁 ディレクトリ構成

```
client/
├── src/
│   ├── pages/          # ページコンポーネント
│   ├── types/          # 型定義
│   ├── App.tsx         # ルートコンポーネント
│   └── main.tsx        # エントリーポイント
└── package.json
```

## ✨ 実装済み機能

- ✅ ホームページ（名前入力）
- ✅ ロビーページ（ゲームモード選択）
- ✅ ゲームページ（ポーカーテーブルUI）
- ✅ レスポンシブデザイン
- ✅ アニメーション

## 🔄 次のステップ

- [ ] WebSocket接続
- [ ] ゲーム状態の同期
- [ ] AI実装
- [ ] カードアニメーション
- [ ] チャット機能
