# Papersmith Agent

![Coverage](https://img.shields.io/badge/coverage-91%25-brightgreen)
![Tests](https://img.shields.io/badge/tests-372%20passed-brightgreen)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)

完全ローカルで動作する自律型論文解析エージェントシステム

## 概要

Papersmith Agentは、arXiv APIから論文データを自動取得し、Chromaベクターストア、RAG（Retrieval-Augmented Generation）を活用して、論文の検索・解析・質問応答を提供する完全ローカル実行可能なシステムです。

### 現在の機能（Phase 1完了）

- **論文検索と取得**: arXiv APIを使用した論文検索とPDF自動ダウンロード
- **テキスト処理**: IMRaD構造に基づくセクション分割とチャンク化
- **Embedding生成**: multilingual-e5-baseによる多言語対応
- **ベクターストア**: Chromaを使用した高速な類似度検索
- **RAG（検索拡張生成）**: 論文内容に基づく質問応答
- **FastAPI**: RESTful APIによるプログラマティックアクセス
- **完全ローカル実行**: Docker環境での完全ローカル動作（GPU対応）

### 今後の機能（Phase 2以降）

- **Web UI**: Streamlitによる直感的なユーザーインターフェース（Phase 2 - 進行中）
- **Corrective Retrieval**: Support ScoreとHyDEによる検索精度向上（Phase 3）
- **マルチエージェント**: LangGraphによる複数ワークフローの自動振り分け（Phase 4）
- **学習サポート**: Cornell NotesとQuiz自動生成（Phase 4）
- **Daily Digest**: 最新論文の自動要約レポート（Phase 4）

## 必要要件

### 最小要件（外部API使用）

- Docker & Docker Compose
- 8GB RAM以上
- 10GB以上のディスク空き容量
- Gemini API キー（無料）または OpenAI API キー

### ローカルモデル使用時

- 16GB RAM以上（推奨32GB以上）
- 50GB以上のディスク空き容量
- **Mac**: Apple Silicon（M1/M2/M3）推奨
- **Linux/Windows**: NVIDIA GPU + CUDA（オプション）

## セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd papersmith-agent
```

### 2. 環境変数の設定

```bash
cp .env.template .env
```

`.env`ファイルを編集して、必要な設定を行います：

#### オプション1: Gemini API使用（推奨・無料）

```bash
# バックエンド設定
LLM_BACKEND=gemini
EMBEDDING_BACKEND=gemini

# Gemini APIキー（https://makersuite.google.com/app/apikey で取得）
GOOGLE_API_KEY=your_api_key_here
```

#### オプション2: OpenAI API使用

```bash
# バックエンド設定
LLM_BACKEND=openai
EMBEDDING_BACKEND=openai

# OpenAI APIキー
OPENAI_API_KEY=your_api_key_here
```

#### オプション3: ローカルモデル使用

**Mac（Apple Silicon）:**
```bash
# MLXバックエンド（Mac GPU使用）
LLM_BACKEND=local-mlx
EMBEDDING_BACKEND=local-cpu

# モデル設定
LLM_MODEL_NAME=mlx-community/Llama-3-ELYZA-JP-8B-4bit
EMBEDDING_MODEL_NAME=intfloat/multilingual-e5-base
```

**Linux/Windows（NVIDIA GPU）:**
```bash
# CUDAバックエンド
LLM_BACKEND=local-cuda
EMBEDDING_BACKEND=local-cuda

# モデル設定
LLM_MODEL_NAME=elyza/Llama-3-ELYZA-JP-8B
EMBEDDING_MODEL_NAME=intfloat/multilingual-e5-base
```

**CPU のみ:**
```bash
# CPUバックエンド
LLM_BACKEND=local-cpu
EMBEDDING_BACKEND=local-cpu

# モデル設定
LLM_MODEL_NAME=elyza/Llama-3-ELYZA-JP-8B
EMBEDDING_MODEL_NAME=intfloat/multilingual-e5-base
```

### 3. バックエンドの選択ガイド

| バックエンド | 推奨環境 | メリット | デメリット | コスト |
|------------|---------|---------|-----------|--------|
| **gemini** | 全環境 | 無料、高速、セットアップ簡単 | インターネット必須 | 無料 |
| **openai** | 全環境 | 高品質、高速 | インターネット必須 | 有料 |
| **local-mlx** | Mac M1/M2/M3 | 高速、オフライン動作 | Macのみ、初回DL大 | 無料 |
| **local-cuda** | NVIDIA GPU | 高速、オフライン動作 | GPU必須、初回DL大 | 無料 |
| **local-cpu** | 全環境 | オフライン動作 | 非常に遅い | 無料 |

**推奨設定:**
- **開発・テスト**: `gemini`（無料、高速）
- **Mac本番**: `local-mlx`（オフライン、高速）
- **GPU本番**: `local-cuda`（オフライン、高速）
- **本番（GPU無し）**: `gemini` または `openai`

### 4. Dockerコンテナの起動

#### オプション1: API + UI（推奨）

両方のサービスを同時に起動：

```bash
docker-compose up -d
```

- FastAPI: `http://localhost:8000`
- Streamlit UI: `http://localhost:8501`

#### オプション2: APIのみ

```bash
docker-compose up -d papersmith-api
```

#### オプション3: UIのみ（APIが別途起動している場合）

```bash
docker-compose up -d papersmith-ui
```

**注意:**
- 外部API（gemini/openai）使用時は即座に起動します
- ローカルモデル使用時は、初回起動時にモデルのダウンロードに時間がかかります（数GB〜数十GB）

### 5. ヘルスチェック

```bash
curl http://localhost:8000/health
```

レスポンス例：
```json
{
  "status": "healthy",
  "index_ready": true
}
```

### 6. ログの確認

```bash
# 全サービスのログ
docker-compose logs -f

# APIのみ
docker-compose logs -f papersmith-api

# UIのみ
docker-compose logs -f papersmith-ui
```

## 使用方法

### Web UI（推奨）

#### Docker Compose使用（推奨）

最も簡単な方法：

```bash
docker-compose up -d
```

ブラウザで `http://localhost:8501` にアクセスしてください。

#### ローカル実行

開発時やDocker未使用の場合：

```bash
# FastAPI サーバーを起動（別ターミナル）
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Streamlit UIを起動
./run_ui.sh
# または
streamlit run ui/app.py
```

**現在の機能（Phase 2完了）:**
- ✅ ホームページ（システム概要、API接続確認）
- ✅ 論文検索ページ（キーワード検索、ダウンロード）
- ✅ RAG質問応答ページ（質問入力、回答表示）
- ✅ 論文一覧ページ（インデックス済み論文の表示）
- ✅ エラーハンドリングとローディング状態

#### UI使用方法

**1. ホームページ**
- システム概要とAPI接続状態を確認
- サイドバーから各機能ページへナビゲーション
- インデックス済みドキュメント数を表示

**2. 論文検索ページ（📖 論文検索）**
- キーワードで論文を検索（例: "transformer attention mechanism"）
- 最大取得件数を調整（1-50件）
- 検索結果をカード形式で表示
- 各論文の要約を展開表示
- 「ダウンロード」ボタンでPDF取得とインデックス化を実行
- ダウンロード進捗をリアルタイム表示

**3. RAG質問応答ページ（💬 RAG質問応答）**
- インデックス化された論文に対して質問を入力
- 特定の論文に絞り込み検索（マルチセレクト）
- 取得チャンク数（top_k）を調整
- LLMが生成した回答を表示
- 参照元チャンクを展開表示（スコア、セクション情報付き）
- サポートスコアと試行回数をメトリクス表示

**4. 論文一覧ページ（📚 論文一覧）**
- インデックス化された論文の一覧を表示
- 並び替え機能（新しい順、古い順、タイトル順）
- 各論文の詳細情報を展開表示
- インデックス統計情報をサイドバーに表示

詳細な使用ガイドは [docs/UI_GUIDE.md](docs/UI_GUIDE.md) を参照してください。

### API（プログラマティックアクセス）

#### 1. ヘルスチェック

システムが正常に起動しているか確認：

```bash
curl http://localhost:8000/health
```

### 2. 論文検索

arXivから論文を検索：

```bash
curl -X POST http://localhost:8000/papers/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "max_results": 5
  }'
```

### 3. 論文ダウンロードとインデックス化

PDFをダウンロードし、ベクターストアにインデックス化：

```bash
curl -X POST http://localhost:8000/papers/download \
  -H "Content-Type: application/json" \
  -d '{
    "arxiv_id": "2301.00001"
  }'
```

### 4. RAG質問応答

インデックス化された論文に対して質問：

```bash
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "この論文の主な貢献は何ですか？",
    "arxiv_ids": ["2301.00001"],
    "top_k": 5
  }'
```

### 5. インタラクティブAPIドキュメント

ブラウザで以下にアクセス：

```
http://localhost:8000/docs
```

Swagger UIで全エンドポイントを試すことができます。

## プロジェクト構造

```
papersmith-agent/
├── .kiro/
│   ├── specs/            # プロジェクト仕様書
│   └── steering/         # テストガイドライン
├── ui/                   # Streamlit Web UI
│   ├── app.py            # メインアプリケーション
│   ├── config.py         # API接続設定
│   ├── pages/            # UIページ
│   └── README.md         # UI使用方法
├── src/
│   ├── api/              # FastAPI endpoints
│   │   ├── main.py       # メインアプリケーション
│   │   └── index_holder.py  # インデックス管理
│   ├── services/         # Service layer
│   │   ├── paper_service.py     # 論文管理
│   │   ├── rag_service.py       # RAG処理
│   │   ├── llm_service.py       # LLM推論
│   │   └── embedding_service.py # Embedding生成
│   ├── models/           # Data models
│   │   ├── paper.py      # 論文モデル
│   │   ├── rag.py        # RAGモデル
│   │   └── config.py     # 設定モデル
│   ├── clients/          # External API clients
│   │   ├── arxiv_client.py   # arXiv API
│   │   └── chroma_client.py  # Chroma DB
│   └── utils/            # Utilities
│       ├── errors.py     # エラー定義
│       └── logger.py     # ロギング
├── tests/
│   ├── unit/             # ユニットテスト
│   ├── integration/      # 統合テスト
│   └── e2e/              # E2Eテスト
├── data/
│   └── chroma/           # Chromaデータ永続化
├── cache/
│   ├── pdfs/             # ダウンロード済みPDF
│   └── metadata/         # キャッシュ済みメタデータ
├── models/               # ダウンロード済みLLMモデル
├── docker-compose.yml    # Docker構成
├── Dockerfile            # Dockerイメージ定義
├── requirements.txt      # Python依存関係
├── demo_phase1.py        # Phase 1デモスクリプト
└── README.md             # このファイル
```

## 開発

### ローカル開発環境

```bash
# 仮想環境の作成
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt

# 開発サーバーの起動
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### テストの実行

```bash
# 全テスト実行（カバレッジ付き）
uv run pytest --cov=src --cov-report=html --cov-report=term

# ユニットテストのみ（高速）
uv run pytest tests/unit -m unit

# 統合テスト
uv run pytest tests/integration -m integration

# E2Eテスト
uv run pytest tests/e2e -m e2e

# 並列実行（高速化）
uv run pytest -n auto

# スローテストをスキップ（高速イテレーション）
uv run pytest -m "not slow"

# 実際のAPI接続テスト（要APIキー）
uv run pytest -m slow -v

# カバレッジレポート確認
open htmlcov/index.html  # macOS
# または
xdg-open htmlcov/index.html  # Linux
```

**テストカバレッジ目標:**
- 全体: 85%+ ✅ (現在: 91%)
- Services: 90%+ ✅
- API Endpoints: 85%+ ✅
- Models: 95%+ ✅
- Clients: 80%+ ✅

**テスト統計:**
- 総テスト数: 372 passed, 5 skipped
- 実行時間: ~4分22秒
- カバレッジ: 91.20%
open htmlcov/index.html  # macOS
```

**カバレッジ目標:**
- 全体: 85%+
- Services: 90%+
- API Endpoints: 85%+
- Models: 95%+

### Phase 1の完了状況

Phase 1（基本MVP）は完了しています：

- ✅ 全14タスク完了
- ✅ 29/29テスト成功
- ✅ 実機能デモ成功
- ✅ ドキュメント完備

### Phase 2の完了状況

Phase 2（UI・実用化）は完了しています：

- ✅ 全8タスク完了（Task 15-22）
- ✅ Streamlit Web UI実装
- ✅ 論文検索、RAG質問応答、論文一覧機能
- ✅ エラーハンドリングとローディング状態
- ✅ Docker統合
- ✅ 詳細なドキュメント作成

詳細は `.kiro/specs/papersmith-agent/` を参照してください。

## トラブルシューティング

### Dockerビルドエラー

**症状**: `apt-get update` でエラーが発生

**解決策**: Dockerfileが最新版（python:3.11-slim）を使用していることを確認
```bash
# キャッシュをクリアして再ビルド
docker-compose build --no-cache
```

### API接続エラー

**症状**: `GOOGLE_API_KEY is required for gemini backend`

**解決策**: `.env`ファイルにAPIキーを設定
```bash
# .envファイルを編集
GOOGLE_API_KEY=your_actual_api_key_here
```

### メモリ不足エラー

**症状**: ローカルモデル使用時にメモリ不足

**解決策**: 外部APIに切り替え
```bash
# .envファイルを編集
LLM_BACKEND=gemini
EMBEDDING_BACKEND=gemini
GOOGLE_API_KEY=your_api_key_here
```

### Mac でローカルモデルが遅い

**症状**: `local-cpu` バックエンドが非常に遅い

**解決策**: MLXバックエンドに切り替え（Apple Silicon のみ）
```bash
# .envファイルを編集
LLM_BACKEND=local-mlx

# MLXをインストール（ローカル実行時）
pip install mlx mlx-lm
```

### GPU が認識されない（CUDA使用時）

**症状**: `local-cuda` バックエンドでGPUが使用されない

**解決策**: 
1. NVIDIA Container Toolkitのインストール確認
```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

2. docker-compose.ymlにGPU設定を追加（必要に応じて）
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

### モデルのダウンロードが遅い

**症状**: ローカルモデル初回起動時に時間がかかる

**解決策**: 
- 外部API（gemini）を使用して即座に開始
- または、ログを確認してダウンロード進捗を監視
```bash
docker-compose logs -f papersmith-api
```

## ドキュメント

### プロジェクト仕様

- [要件定義](.kiro/specs/papersmith-agent/requirements.md) - 全要件の詳細
- [設計書](.kiro/specs/papersmith-agent/design.md) - アーキテクチャと設計
- [タスクリスト](.kiro/specs/papersmith-agent/tasks.md) - 実装タスク一覧

### 使用ガイド

- [UI使用ガイド](docs/UI_GUIDE.md) - Web UIの詳細な使用方法
- [Dockerガイド](docs/DOCKER_GUIDE.md) - Docker統合とトラブルシューティング
- [エラーハンドリング](docs/ERROR_HANDLING.md) - エラーハンドリングパターン

### プロジェクト管理

- [プロジェクトステータス](docs/PROJECT_STATUS.md) - 全体の進捗状況と次のアクション

### 開発ガイド

- [開発ガイドライン](.kiro/steering/development-guidelines.md) - テスト方針、実行確認、タスク完了基準

## ライセンス

MIT License

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。
