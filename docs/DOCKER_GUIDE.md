# Docker統合ガイド

## 概要

Papersmith Agentは、Docker Composeを使用してFastAPI（バックエンド）とStreamlit（フロントエンド）の両方を簡単に起動できます。

## アーキテクチャ

```
┌─────────────────────────────────────────┐
│         Docker Compose                  │
│                                         │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ papersmith-  │  │ papersmith-  │   │
│  │    api       │  │     ui       │   │
│  │              │  │              │   │
│  │ FastAPI      │◄─┤ Streamlit    │   │
│  │ Port: 8000   │  │ Port: 8501   │   │
│  │              │  │              │   │
│  │ GPU対応      │  │              │   │
│  └──────────────┘  └──────────────┘   │
│         │                               │
│         ▼                               │
│  ┌──────────────┐                      │
│  │  Volumes     │                      │
│  │  - data/     │                      │
│  │  - cache/    │                      │
│  │  - models/   │                      │
│  └──────────────┘                      │
└─────────────────────────────────────────┘
```

## マルチバックエンド対応

システムは複数のLLM/Embeddingバックエンドをサポート：

| バックエンド | 説明 | 推奨環境 | GPU要件 |
|------------|------|---------|---------|
| **gemini** | Google Gemini API（無料） | 全環境 | 不要 |
| **openai** | OpenAI API | 全環境 | 不要 |
| **local-cpu** | ローカルCPU実行 | 全環境 | 不要（遅い） |
| **local-mlx** | Mac GPU（MLX） | Apple Silicon | Mac GPU |
| **local-cuda** | NVIDIA GPU（CUDA） | Linux/Windows | NVIDIA GPU |

**デフォルト**: `gemini`（無料、高速、セットアップ簡単）

## サービス構成

### papersmith-api

- **ベースイメージ**: python:3.11-slim
- **ポート**: 8000
- **GPU**: オプション（バックエンドによる）
- **役割**: FastAPI RESTful API、LLM推論、Embedding生成、RAG処理

### papersmith-ui

- **ベースイメージ**: python:3.11-slim（base stage）
- **ポート**: 8501
- **役割**: Streamlit Web UI、ユーザーインターフェース

### ネットワーク

- **papersmith-network**: 両サービス間の通信用ブリッジネットワーク
- UIからAPIへは `http://papersmith-api:8000` でアクセス

## 起動方法

### 1. 環境変数の設定

```bash
cp .env.template .env
```

`.env`ファイルを編集：

#### オプション1: Gemini API使用（推奨）

```bash
# バックエンド設定
LLM_BACKEND=gemini
EMBEDDING_BACKEND=gemini

# Gemini APIキー（https://makersuite.google.com/app/apikey で取得）
GOOGLE_API_KEY=your_api_key_here

# API URL（Docker Compose使用時）
PAPERSMITH_API_URL=http://papersmith-api:8000
```

#### オプション2: ローカルモデル使用

```bash
# Mac（Apple Silicon）
LLM_BACKEND=local-mlx
EMBEDDING_BACKEND=local-cpu

# Linux/Windows（NVIDIA GPU）
LLM_BACKEND=local-cuda
EMBEDDING_BACKEND=local-cuda

# CPU のみ
LLM_BACKEND=local-cpu
EMBEDDING_BACKEND=local-cpu
```

### 2. 両方のサービスを起動

```bash
docker compose up -d
```

### 3. APIのみ起動

```bash
docker compose up -d papersmith-api
```

### 4. UIのみ起動（APIが既に起動している場合）

```bash
docker compose up -d papersmith-ui
```

## アクセス

- **FastAPI**: http://localhost:8000
- **FastAPI Docs**: http://localhost:8000/docs
- **Streamlit UI**: http://localhost:8501

## ログの確認

```bash
# 全サービス
docker compose logs -f

# APIのみ
docker compose logs -f papersmith-api

# UIのみ
docker compose logs -f papersmith-ui
```

## 停止と削除

```bash
# 停止
docker compose stop

# 停止して削除
docker compose down

# ボリュームも削除（データを完全にクリア）
docker compose down -v
```

## ボリュームマウント

### API

- `./src:/app/src` - ソースコード（開発用）
- `./data:/app/data` - Chromaデータベース（永続化）
- `./cache:/app/cache` - PDF・メタデータキャッシュ（永続化）
- `./models:/app/models` - ダウンロード済みモデル（永続化）

### UI

- `./ui:/app/ui` - UIソースコード（開発用）

## マルチステージビルド

Dockerfileは、効率的なイメージサイズのためにマルチステージビルドを使用：

1. **base**: 共通の依存関係をインストール
2. **api**: FastAPIアプリケーション用
3. **ui**: Streamlitアプリケーション用

## トラブルシューティング

### UIがAPIに接続できない

**症状**: UI起動時に「API接続エラー」が表示される

**解決策**:
1. APIが起動しているか確認: `docker compose ps`
2. APIのログを確認: `docker compose logs papersmith-api`
3. ネットワーク接続を確認: `docker compose exec papersmith-ui ping papersmith-api`

### API接続エラー

**症状**: `GOOGLE_API_KEY is required for gemini backend`

**解決策**:
1. `.env`ファイルにAPIキーを設定
2. コンテナを再起動: `docker compose restart papersmith-api`

### GPUが認識されない（CUDA使用時）

**症状**: `local-cuda`バックエンドでGPU関連のエラーが発生

**解決策**:
1. NVIDIA Container Toolkitがインストールされているか確認
2. 外部API（gemini）に切り替え: `.env`で`LLM_BACKEND=gemini`を設定

### ポートが既に使用されている

**症状**: `port is already allocated`エラー

**解決策**:
1. 既存のプロセスを停止: `lsof -ti:8000 | xargs kill -9`
2. または、docker-compose.ymlでポートを変更

### モデルのダウンロードが遅い

**症状**: 初回起動時に長時間かかる

**解決策**:
- 正常な動作です。ログで進捗を確認: `docker compose logs -f papersmith-api`
- モデルは`./models`ディレクトリにキャッシュされ、次回以降は高速に起動します

## 開発モード

ソースコードの変更を即座に反映させるには：

```bash
# ホットリロード有効でAPI起動
docker compose up papersmith-api

# 別ターミナルでUI起動
docker compose up papersmith-ui
```

ボリュームマウントにより、ローカルの変更がコンテナ内に即座に反映されます。

## 本番環境への展開

本番環境では、以下の変更を推奨：

1. **ボリュームマウントの削除**: ソースコードをイメージに含める
2. **環境変数の保護**: `.env`ファイルをGit管理から除外
3. **リソース制限**: `deploy.resources.limits`を設定
4. **ヘルスチェック**: 既に設定済み
5. **再起動ポリシー**: `restart: unless-stopped`（既に設定済み）

## 参考

- [Docker Compose公式ドキュメント](https://docs.docker.com/compose/)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
