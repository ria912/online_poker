online_poker/
├── server/                    # バックエンド
│   ├── app/                   # アプリケーションコード
│   │   ├── api/              # API エンドポイント
│   │   ├── core/             # 設定・セキュリティ
│   │   ├── models/           # データベースモデル
│   │   ├── schemas/          # Pydanticスキーマ
│   │   ├── services/         # ビジネスロジック
│   │   ├── game/             # ゲームロジック（メイン実装）
│   │   │   ├── domain/       # ドメインモデル
│   │   │   │   ├── action.py        # プレイヤーアクション
│   │   │   │   ├── deck.py          # デッキとカード
│   │   │   │   ├── enum.py          # 列挙型定義
│   │   │   │   ├── game_state.py    # ゲーム状態管理
│   │   │   │   ├── player.py        # プレイヤー情報
│   │   │   │   ├── seat.py          # 座席管理
│   │   │   │   └── table.py         # テーブル管理
│   │   │   └── services/     # ゲームサービス
│   │   │       ├── betting_service.py    # ベッティング処理
│   │   │       ├── dealer_service.py     # ディーラー処理
│   │   │       ├── game_service.py       # ゲーム全体管理
│   │   │       ├── hand_evaluator.py     # ハンド評価（treys）
│   │   │       ├── hand_service.py       # ハンド関連処理
│   │   │       ├── poker_engine.py       # ポーカーエンジン
│   │   │       └── turn_manager.py       # ターン管理
│   │   └── websocket/        # WebSocket処理
│   ├── tests/                # テストコード
│   │   └── test_bb_option.py # BBオプションテスト
│   ├── requirements.txt      # 依存関係
│   └── main.py               # アプリケーションエントリポイント
├── client/                    # フロントエンド（将来実装）
└── AGENT.md                  # このファイル
# Online Poker Game - AGENT.md

---
このファイルは「全体像・設計思想・進捗・学習ガイドの要約」です。
詳細・実装例・FAQは各README（game/domain/services）を参照してください。
---

■ 目的・進捗
- 最終目標：マルチプレイヤー対応オンラインポーカー（リアルタイム・複数ルーム・AI・ランキング）
- 現状：テキサスホールデムのエンジン作成中

■ 設計思想（要点）
- DDD（ドメイン駆動設計）／SRP（単一責任原則）／疎結合
- Domain層：ゲーム状態・テーブル・座席・プレイヤー・カード・アクション
- Services層：進行・ディーラー・ベッティング・ターン・ハンド評価
- API/WebSocket層：REST・リアルタイム通信

■ 学習・開発ガイド
- 設計思想・責務・実装例は各READMEに集約
- サンプルコード・API仕様・テスト例もREADME参照

■ 開発環境・運用
- 仮想環境・依存関係・起動方法は `game/README.md`
- コード品質：black / isort / mypy / pytest

■ FAQ・トラブル対応
- インポート・依存関係・テスト失敗はREADMEのFAQ参照

■ 参考資料
- FastAPI / treys / Pydantic / WebSocket / PokerNews

---
このファイルだけで「全体像・設計思想・進捗」を最短把握。詳細は必ず各READMEへ。