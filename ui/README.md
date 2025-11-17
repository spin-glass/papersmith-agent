# Papersmith Agent - Streamlit UI

完全ローカルで動作する論文解析システムのWeb UIです。

## 構成

```
ui/
├── app.py              # メインアプリケーション（ホームページ）✅
├── config.py           # FastAPI接続設定 ✅
├── pages/              # Streamlitページ
│   ├── 1_search.py     # 論文検索ページ ✅
│   ├── 2_rag.py        # RAG質問応答ページ ✅
│   └── 3_papers.py     # 論文一覧ページ ✅
├── components/         # 共通UIコンポーネント ✅
│   ├── paper_card.py   # 論文カード
│   ├── search_form.py  # 検索フォーム
│   ├── rag_form.py     # RAG質問フォーム
│   └── styles.py       # 共通スタイル
└── utils/              # ユーティリティ ✅
    └── error_handler.py # エラーハンドリング
```

## 実装状況

### ✅ Phase 2完了（UI・実用化）

**Task 15: 基本セットアップ**
- FastAPI接続設定（config.py）
- ホームページ実装（app.py）
- システム概要表示
- API接続状態確認
- ナビゲーションメニュー
- 起動スクリプト（run_ui.sh）

**Task 16: 論文検索UI**
- 検索フォーム（キーワード入力、最大取得件数設定）
- POST /papers/search API呼び出し
- 検索結果の表示（カード形式）
- 各論文のダウンロードボタン
- ダウンロード進捗の表示

**Task 17: RAG質問応答UI**
- 質問入力フォーム
- インデックス済み論文の選択（マルチセレクト）
- POST /rag/query API呼び出し
- 回答の表示（マークダウン形式）
- 参照元チャンクの表示（エクスパンダー）

**Task 18: 論文一覧UI**
- インデックス済み論文の一覧表示
- 各論文の詳細情報（タイトル、著者、年）
- 並び替え機能（新しい順、古い順、タイトル順）

**Task 19: UIコンポーネント**
- 論文カード（paper_card.py）
- 検索フォーム（search_form.py）
- RAG質問フォーム（rag_form.py）
- 共通スタイル（styles.py）

**Task 20: エラーハンドリング**
- API呼び出しのエラーハンドリング
- ローディング状態の表示（st.spinner、st.progress）
- エラーメッセージの改善（日本語、わかりやすい説明）
- 503エラー時の適切な表示

**Task 21: Docker統合**
- docker-compose.ymlにstreamlitサービスを追加
- ポート設定（FastAPI: 8000、Streamlit: 8501）
- ボリュームマウントの設定

**Task 22: Phase 2統合テストとドキュメント**
- UI使用方法のドキュメント化
- 詳細な使用ガイド（UI_GUIDE.md）
- README.mdの更新

## 起動方法

### 1. FastAPI サーバーを起動

```bash
# Docker Composeを使用する場合
docker-compose up

# または直接起動
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### 2. Streamlit UIを起動

```bash
streamlit run ui/app.py
```

デフォルトでは `http://localhost:8501` でアクセスできます。

## 環境変数

- `PAPERSMITH_API_URL`: FastAPI のベースURL（デフォルト: `http://localhost:8000`）

## 機能

### ホームページ（実装済み）
- システム概要の表示
- API接続状態の確認
- ナビゲーション

### 論文検索（Task 16で実装予定）
- キーワード検索
- 検索結果の表示
- PDFダウンロードとインデックス化

### RAG質問応答（Task 17で実装予定）
- 質問入力
- 論文選択
- 回答表示

### 論文一覧（Task 18で実装予定）
- インデックス済み論文の一覧
- 詳細情報表示

## 要件

- Python 3.11+
- streamlit 1.31.0+
- httpx 0.26.0+
- FastAPI サーバーが起動していること

## 開発

新しいページを追加する場合は、`ui/pages/` ディレクトリに `N_pagename.py` という形式でファイルを作成してください。Streamlitが自動的にサイドバーに追加します。
