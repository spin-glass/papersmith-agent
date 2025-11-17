# Requirements Document

## Introduction

Papersmith Agentは、完全ローカルで動作する論文解析システムです。arXiv APIから論文を取得し、Chromaベクターストア、RAG（Retrieval-Augmented Generation）を活用して、論文の検索・解析・質問応答を提供します。

## Glossary

- **Chroma**: ローカルベクターデータベース
- **RAG**: Retrieval-Augmented Generation（検索拡張生成）
- **IMRaD**: Introduction, Methods, Results, and Discussion（論文構造）
- **uv**: Rust製の高速Pythonパッケージマネージャー
- **Backend**: LLM/Embedding処理を実行する基盤（gemini、openai、local-cpu、local-mlx、local-cuda）
- **MLX**: Apple Silicon用の機械学習フレームワーク
- **CUDA**: NVIDIA GPU用の並列計算プラットフォーム
- **Gemini API**: Googleの無料LLM API
- **pyproject.toml**: Python標準のプロジェクト設定ファイル
- **uv.lock**: uvが生成する依存関係のロックファイル

## Requirements

### Requirement 1: 論文データ取得

**User Story:** 研究者として、特定のテーマやキーワードで論文を検索し、メタデータとPDFを自動取得したい。これにより手動でのダウンロード作業を削減できる。

#### Acceptance Criteria

1. WHEN Userがキーワードを指定して検索を実行する時、THE System SHALL arXiv APIを使用して関連論文のメタデータとPDF URLを取得する
2. WHEN 論文のDOIが利用可能な時、THE System SHALL CrossRef APIを使用して引用関係とメタデータを取得する
3. WHEN 論文IDが指定された時、THE System SHALL Semantic Scholar APIを使用して概要・引用・メタデータを取得する
4. WHEN 論文PDFのURLが取得された時、THE System SHALL PDFファイルをローカルストレージにダウンロードして保存する
5. WHEN 論文データが取得された時、THE System SHALL メタデータ（arxiv_id、title、authors、year）をローカルキャッシュに保存する

### Requirement 2: ベクター検索とRAG基盤

**User Story:** 研究者として、取得した論文から効率的に情報を検索し、質問に対する正確な回答を得たい。これにより論文の理解を深めることができる。

#### Acceptance Criteria

1. WHEN 論文PDFが処理される時、THE System SHALL IMRaD構造に基づいてセクション単位でテキストをチャンク化する
2. WHEN テキストチャンクが生成された時、THE System SHALL 各チャンクに対してembeddingを生成しChromaベクターストアに保存する
3. WHEN チャンクがベクターストアに保存される時、THE System SHALL メタデータ（arxiv_id、title、authors、year、section、chunk_id）を含める
4. WHEN Userが質問を入力する時、THE System SHALL Chromaベクターストアから関連チャンクを検索する
5. WHEN 検索結果が取得された時、THE System SHALL LLMを使用して検索結果に基づく回答を生成する

### Requirement 3: Web UI（実用化）

**User Story:** 研究者として、コマンドラインではなくWebブラウザから直感的に論文を検索・解析したい。これにより日常的な研究活動で実用的に使えるようになる。

#### Acceptance Criteria

1. WHEN Userがブラウザでアクセスする時、THE System SHALL シンプルで使いやすいWeb UIを表示する
2. WHEN Userが論文を検索する時、THE System SHALL 検索結果を視覚的に表示する
3. WHEN Userが論文をダウンロードする時、THE System SHALL 進捗状況をリアルタイムで表示する
4. WHEN Userが質問を入力する時、THE System SHALL RAG回答を見やすく表示する
5. WHEN 処理が実行される時、THE System SHALL ローディング状態を適切に表示する

### Requirement 4: Corrective Retrieval（RAG強化）

**User Story:** 研究者として、RAG検索の精度が低い場合でも、自動的に再検索して正確な回答を得たい。これにより検索失敗による時間の無駄を削減できる。

#### Acceptance Criteria

1. WHEN RAG検索が実行された時、THE System SHALL 検索結果に対してSupport Score（0-1）を計算する
2. IF Support Scoreが閾値θ未満の時、THEN THE System SHALL HyDEを使用して仮想論文サマリーを生成し再検索を実行する
3. WHEN 再検索が実行された時、THE System SHALL 2回目のSupport Scoreを計算する
4. IF 両方のSupport Scoreが閾値未満の時、THEN THE System SHALL 日本語で改善ポイントを含むNo-answerメッセージを返す
5. WHEN 検索が成功した時、THE System SHALL Support ScoreとAttempts回数をメタデータとして保存する

### Requirement 5: Message Routerとワークフロー制御

**User Story:** 研究者として、異なるタイプの質問や要求を自動的に適切な処理フローに振り分けてほしい。これにより複雑なコマンドを覚える必要がなくなる。

#### Acceptance Criteria

1. WHEN Userがメッセージを入力する時、THE System SHALL Message Routerを使用してメッセージタイプを分類する
2. WHEN メッセージが`search:`で始まる時、THE System SHALL 論文検索ワークフローを実行する
3. WHEN メッセージが`compare:`で始まる時、THE System SHALL 複数論文比較分析ワークフローを実行する
4. WHEN メッセージが`prereq:`で始まる時、THE System SHALL 背景知識収集ワークフローを実行する
5. WHEN メッセージが`net:`で始まる時、THE System SHALL 引用ネットワーク構築ワークフローを実行する
6. WHEN メッセージが特定のプレフィックスを持たない時、THE System SHALL RAG QAワークフロー（Corrective Retrieval付き）を実行する

### Requirement 6: 学習サポート機能

**User Story:** 学習者として、論文から自動的にCornell NotesやQuizを生成してほしい。これにより効率的に論文内容を学習できる。

#### Acceptance Criteria

1. WHEN 論文が解析された時、THE System SHALL Cornell Notes形式の学習ノートを生成する
2. WHEN Cornell Notesが生成される時、THE System SHALL 主要ポイント、詳細、要約の3セクションを含める
3. WHEN 論文が解析された時、THE System SHALL 論文内容に基づいて2-3問のQuizを生成する
4. WHEN Quizが生成される時、THE System SHALL 各問題に対して正解と解説を含める
5. IF LLMによる生成が失敗した時、THEN THE System SHALL 基本的なサマリーのみを提供するgraceful degradationを実行する

### Requirement 7: Daily Digest

**User Story:** 研究者として、毎日最新の論文を自動的に収集・要約したレポートを受け取りたい。これにより最新研究動向を効率的に追跡できる。

#### Acceptance Criteria

1. WHEN Digest生成が要求された時、THE System SHALL 指定されたカテゴリと日数で最新arXiv論文を取得する
2. WHEN 論文リストが取得された時、THE System SHALL NGキーワードとOKキーワードでフィルタリングを実行する
3. WHEN フィルタリングが完了した時、THE System SHALL LLMを使用して各論文の日本語要約を生成する
4. WHEN 要約が生成された時、THE System SHALL DigestItemとして整形する
5. WHEN DigestItemが生成された時、THE System SHALL 非同期でPDF、セクション解析、フルテキストのPrefetchを開始する

### Requirement 8: ストリーミングレスポンス

**User Story:** ユーザーとして、長時間かかる処理の進捗状況をリアルタイムで確認したい。これにより処理が進行していることを確認でき安心できる。

#### Acceptance Criteria

1. WHEN RAGクエリが実行される時、THE System SHALL SSE（Server-Sent Events）を使用してストリーミングレスポンスを提供する
2. WHEN ストリーミング中、THE System SHALL `status`フィールドでワークフローステップを送信する
3. WHEN ストリーミング中、THE System SHALL `content`フィールドで50-80文字のチャンクを送信する
4. WHEN 処理が完了した時、THE System SHALL `done`フラグをtrueに設定して送信する
5. WHEN Message Routerが実行される時、THE System SHALL SSEでルーティング情報を送信する

### Requirement 9: FastAPI基盤とインデックス管理

**User Story:** 開発者として、安定したAPIレイヤーとインデックス管理機能を持つシステムを構築したい。これによりシステムの信頼性と保守性が向上する。

#### Acceptance Criteria

1. WHEN Systemが起動する時、THE System SHALL FastAPIアプリケーションを初期化しChromaインデックスをロードする
2. WHEN インデックスがロード中の時、THE System SHALL 503ステータスコードを返して待機を指示する
3. WHEN `/admin/init-index`エンドポイントが呼ばれた時、THE System SHALL インデックスを再構築する
4. WHEN インデックスが利用可能な時、THE System SHALL InMemoryIndexHolderを通じてアクセスを提供する
5. IF エラーが発生した時、THEN THE System SHALL エラーログを記録し500ステータスコードを返す

### Requirement 10: Docker環境とローカル実行

**User Story:** 開発者として、環境依存を最小化し、どこでも同じように動作するシステムを構築したい。これによりデプロイと共有が容易になる。

#### Acceptance Criteria

1. THE System SHALL Dockerコンテナ内で完全に動作する
2. THE System SHALL 外部APIクライアント（arXiv、CrossRef、Semantic Scholar）を除き、すべての処理をローカルで実行する
3. THE System SHALL ローカルファイルシステムにPDF、キャッシュ、ベクターストアを永続化する
4. THE System SHALL docker-composeを使用して単一コマンドで起動可能である
5. WHERE GPUが利用可能な時、THE System SHALL GPU加速を使用してLLM推論を高速化する

### Requirement 11: 複数論文比較分析

**User Story:** 研究者として、複数の論文を自動的に比較し、貢献・手法・データセットの違いを理解したい。これにより研究の全体像を把握できる。

#### Acceptance Criteria

1. WHEN 複数の論文IDが指定された時、THE System SHALL 各論文のメタデータとコンテンツを取得する
2. WHEN 論文データが取得された時、THE System SHALL ComparisonAgentを使用して貢献を比較する
3. WHEN 論文データが取得された時、THE System SHALL 手法の違いを分析する
4. WHEN 論文データが取得された時、THE System SHALL 使用されたデータセットを比較する
5. WHEN 比較分析が完了した時、THE System SHALL 日本語で構造化された比較レポートを生成する

### Requirement 12: マルチバックエンド対応とGPUオプション化

**User Story:** 開発者として、GPU環境がなくても外部APIを使用してシステムを動作させたい。また、環境に応じて最適なバックエンドを選択したい。これにより開発・本番環境の柔軟性が向上する。

#### Acceptance Criteria

1. THE System SHALL GPU（CUDA）を必須とせず、すべての処理をCPUまたは外部APIで実行可能にする
2. THE System SHALL LLM推論とEmbedding生成で複数バックエンドを選択可能にする（gemini、openai、local-cpu、local-mlx、local-cuda）
3. WHEN 環境変数でバックエンドが指定された時、THE System SHALL 指定されたバックエンドを使用する
4. WHERE Apple Silicon Macで実行される時、THE System SHALL MLXバックエンドを使用可能にする
5. WHERE NVIDIA GPUが利用可能な時、THE System SHALL CUDAバックエンドを使用可能にする
6. WHERE GPUが利用不可能な時、THE System SHALL 外部API（Gemini/OpenAI）またはCPUバックエンドで動作する
7. WHEN 外部API（Gemini）が使用される時、THE System SHALL 無料枠内で動作する
8. THE System SHALL デフォルトバックエンドとしてGemini APIを使用する（無料・高速・セットアップ簡単）

### Requirement 13: パッケージ管理の最新化

**User Story:** 開発者として、高速で信頼性の高いパッケージマネージャーを使用したい。これにより依存関係のインストール時間を大幅に削減できる。

#### Acceptance Criteria

1. THE System SHALL uvをプライマリパッケージマネージャーとして使用する
2. THE System SHALL pyproject.tomlで全てのプロジェクト依存関係を定義する
3. THE System SHALL uv.lockファイルで全ての依存関係バージョンを固定する
4. WHEN 開発者が`uv sync`を実行する時、THE System SHALL 30秒以内に全ての依存関係をインストールする
5. THE System SHALL Python 3.11以上3.13未満をサポートする
6. THE System SHALL 開発用と本番用の依存関係グループを分離する
