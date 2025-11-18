# Implementation Plan

このタスクリストは、Papersmith Agentを段階的に実装するための具体的なコーディングタスクです。Phase 1で最小限のMVPを動かし、Phase 2-3で高度な機能を追加します。

## Phase 1: 基本MVP

- [x] 1. プロジェクト構造とDocker環境のセットアップ
  - プロジェクトディレクトリ構造を作成（src/api, src/services, src/models, src/clients, tests, data, cache）
  - requirements.txtに必要なパッケージを定義（fastapi, uvicorn, chromadb, transformers, torch, sentence-transformers, pydantic, arxiv, httpx, pypdf）
  - Dockerfileを作成（Python 3.11ベース、CUDA対応）
  - docker-compose.ymlを作成（GPU設定、ボリュームマウント）
  - .envファイルのテンプレートを作成
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 2. データモデルの定義
  - src/models/paper.pyにPaperMetadataモデルを実装
  - src/models/rag.pyにSearchResult、RAGResponseモデルを実装
  - src/models/config.pyに設定モデルを実装（ChromaConfig, LLMConfig, EmbeddingConfig）
  - _Requirements: 1.5, 2.3_

- [x] 3. arXiv APIクライアントの実装
  - src/clients/arxiv_client.pyにArxivClientクラスを実装
  - search_papers()メソッドを実装（キーワード検索、max_results対応）
  - get_metadata()メソッドを実装（arxiv_idからメタデータ取得）
  - download_pdf()メソッドを実装（PDF URLからダウンロード、ローカル保存）
  - エラーハンドリングとリトライロジックを実装
  - _Requirements: 1.1, 1.4_

- [x] 4. PaperServiceの実装
  - src/services/paper_service.pyにPaperServiceクラスを実装
  - search_papers()メソッドを実装（ArxivClientを使用）
  - download_pdf()メソッドを実装（キャッシュチェック、重複ダウンロード防止）
  - get_metadata()メソッドを実装（キャッシュ優先、JSON保存）
  - extract_text()メソッドを実装（pypdfでPDFからテキスト抽出）
  - _Requirements: 1.1, 1.4, 1.5_

- [x] 5. EmbeddingServiceの実装
  - src/services/embedding_service.pyにEmbeddingServiceクラスを実装
  - load_model()メソッドを実装（multilingual-e5-baseをロード）
  - embed()メソッドを実装（単一テキストのEmbedding生成）
  - embed_batch()メソッドを実装（バッチ処理で高速化）
  - _Requirements: 2.2_

- [x] 6. Chromaクライアントの実装
  - src/clients/chroma_client.pyにChromaClientクラスを実装
  - initialize()メソッドを実装（コレクション作成、永続化ディレクトリ設定）
  - add()メソッドを実装（embedding、text、metadataを保存）
  - search()メソッドを実装（ベクター検索、arxiv_idsフィルタ、top_k対応）
  - count()メソッドを実装（インデックス内のドキュメント数）
  - _Requirements: 2.2, 2.3, 2.4_

- [x] 7. RAGServiceの実装
  - src/services/rag_service.pyにRAGServiceクラスを実装
  - index_paper()メソッドを実装（テキストをIMRaD構造で分割、チャンク化、Chromaに保存）
  - _split_by_imrad()メソッドを実装（ヒューリスティックなセクション検出）
  - _chunk_text()メソッドを実装（文単位で分割、chunk_size=512）
  - query()メソッドを実装（Chromaベクター検索のラッパー）
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 8. LLMServiceの実装
  - src/services/llm_service.pyにLLMServiceクラスを実装
  - load_model()メソッドを実装（elyza/Llama-3-ELYZA-JP-8Bをロード、float16、device_map="auto"）
  - generate()メソッドを実装（question + contextからプロンプト構築、推論実行）
  - _build_prompt()メソッドを実装（日本語プロンプトテンプレート）
  - _extract_answer()メソッドを実装（生成テキストから回答部分を抽出）
  - _Requirements: 2.5_

- [x] 9. 基本RAG処理の実装
  - src/services/rag_service.pyにbasic_rag_query()関数を実装
  - ベクター検索→コンテキスト構築→LLM推論の基本フローを実装
  - build_context()ヘルパー関数を実装（SearchResultsからコンテキスト文字列を構築）
  - _Requirements: 2.4, 2.5_

- [x] 10. InMemoryIndexHolderの実装
  - src/api/index_holder.pyにInMemoryIndexHolderクラスを実装
  - シングルトンパターンで実装
  - set()、get()、is_ready()、size()メソッドを実装
  - asyncio.Lockで排他制御
  - _Requirements: 8.1, 8.2, 8.4_

- [x] 11. FastAPIエンドポイントの実装（Phase 1）
  - src/api/main.pyにFastAPIアプリケーションを作成
  - startup イベントでChromaインデックスをロード、InMemoryIndexHolderに設定
  - GET /health エンドポイントを実装（index_ready状態を返す）
  - POST /papers/search エンドポイントを実装（PaperServiceを使用）
  - POST /papers/download エンドポイントを実装（PDF取得、テキスト抽出、インデックス化）
  - POST /rag/query エンドポイントを実装（basic_rag_queryを使用）
  - POST /admin/init-index エンドポイントを実装（インデックス再構築）
  - 503エラーハンドリング（インデックス未準備時）
  - _Requirements: 8.1, 8.2, 8.3, 8.5_

- [x] 12. エラーハンドリングとロギング
  - src/utils/errors.pyにカスタム例外クラスを実装（PapersmithError, APIError, IndexNotReadyError, LLMError）
  - src/utils/logger.pyにロガー設定を実装
  - FastAPIのexception_handlerを実装（各エラータイプに対応）
  - _Requirements: 8.5_

- [x] 13. Phase 1統合テスト
  - tests/integration/test_arxiv_integration.pyを作成（実際のarXiv APIを使用）
  - tests/integration/test_chroma_integration.pyを作成（Chromaの保存・検索をテスト）
  - tests/integration/test_rag_pipeline.pyを作成（検索→ダウンロード→インデックス→RAGのE2Eテスト）
  - _Requirements: 1.1, 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 14. READMEとドキュメント作成
  - README.mdを作成（プロジェクト概要、セットアップ手順、使用方法）
  - API仕様書を作成（各エンドポイントの説明、リクエスト/レスポンス例）
  - docker-compose upでの起動手順を記載
  - サンプルクエリを記載
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

## Phase 2: UI・実用化

- [x] 15. Streamlit UIの基本セットアップ
  - ui/ディレクトリ構造を作成
  - requirements.txtにstreamlitを追加
  - ui/app.pyにメインアプリケーションを作成
  - ホームページの実装（システム概要、ナビゲーション）
  - FastAPI接続の設定（httpxクライアント）
  - _Requirements: 3.1_

- [x] 16. 論文検索UIの実装
  - ui/pages/1_search.pyを作成
  - 検索フォームの実装（キーワード入力、max_results設定）
  - POST /papers/search APIの呼び出し
  - 検索結果の表示（カード形式）
  - 各論文のダウンロードボタン
  - ダウンロード進捗の表示（st.spinner）
  - _Requirements: 3.2, 3.3_

- [x] 17. RAG質問応答UIの実装
  - ui/pages/2_rag.pyを作成
  - 質問入力フォーム
  - インデックス済み論文の選択（マルチセレクト）
  - POST /rag/query APIの呼び出し
  - 回答の表示（マークダウン形式）
  - 参照元チャンクの表示（エクスパンダー）
  - _Requirements: 3.4_

- [x] 18. 論文一覧UIの実装
  - ui/pages/3_papers.pyを作成
  - インデックス済み論文の一覧表示
  - 各論文の詳細情報（タイトル、著者、年、チャンク数）
  - 論文の削除機能（オプション）
  - _Requirements: 3.1_

- [x] 19. UIコンポーネントの実装
  - ui/components/paper_card.pyを作成（論文カード）
  - ui/components/search_form.pyを作成（検索フォーム）
  - ui/components/rag_form.pyを作成（RAG質問フォーム）
  - 共通スタイルの定義
  - _Requirements: 3.1, 3.2, 3.4_

- [x] 20. エラーハンドリングとローディング状態の改善
  - API呼び出しのエラーハンドリング
  - ローディング状態の表示（st.spinner、st.progress）
  - エラーメッセージの改善（日本語、わかりやすい説明）
  - 503エラー時の適切な表示
  - _Requirements: 3.5_

- [x] 21. Docker統合とデプロイ
  - docker-compose.ymlにstreamlitサービスを追加
  - Dockerfileの更新（streamlit対応、PYTHONPATH設定）
  - ポート設定（FastAPI: 8000、Streamlit: 8501）
  - ボリュームマウントの設定
  - UIインポートエラーの修正（PYTHONPATH=/app）
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [x] 22. Phase 2統合テストとドキュメント
  - UIの動作確認（手動テスト）
  - スクリーンショットの作成
  - README.mdの更新（UI使用方法）
  - UI_GUIDE.mdの作成（詳細な使用ガイド）
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

## Phase 2.5: マルチバックエンド対応とパッケージ管理最新化

- [x] 22.1. uvパッケージマネージャーへの移行
  - [x] 22.1.1 pyproject.tomlの作成
    - プロジェクトメタデータを定義
    - requirements.txtから依存関係を変換
    - 依存関係を論理的なグループに分類（core、ui、dev）
    - _Requirements: 13.1, 13.2, 13.6_
  - [x] 22.1.2 uv.lockの生成と検証
    - `uv lock`でロックファイル生成
    - `uv sync`で依存関係インストール
    - 既存機能の動作確認
    - _Requirements: 13.3, 13.4_
  - [x] 22.1.3 Dockerfileのuv統合
    - uvのインストールを追加
    - pip installをuv syncに置き換え
    - キャッシュ最適化
    - _Requirements: 13.1, 13.4_
  - [x] 22.1.4 Python 3.12への更新
    - Python 3.12-bookwormベースイメージに変更
    - 依存関係の互換性確認
    - pydanticを2.12.4に更新
    - _Requirements: 13.5_

- [x] 22.2. マルチバックエンド対応の実装
  - [x] 22.2.1 バックエンド抽象化レイヤーの実装
    - LLMServiceにマルチバックエンド対応を追加
    - EmbeddingServiceにマルチバックエンド対応を追加
    - 環境変数による設定（LLM_BACKEND、EMBEDDING_BACKEND）
    - _Requirements: 12.2, 12.3_
  - [x] 22.2.2 Gemini APIバックエンドの実装
    - google-generativeaiパッケージの統合
    - LLMServiceにGeminiバックエンド実装
    - EmbeddingServiceにGeminiバックエンド実装
    - _Requirements: 12.7, 12.8_
  - [x] 22.2.3 OpenAI APIバックエンドの実装
    - openaiパッケージの統合
    - LLMServiceにOpenAIバックエンド実装
    - EmbeddingServiceにOpenAIバックエンド実装
    - _Requirements: 12.2_
  - [x] 22.2.4 ローカルバックエンドの実装
    - local-cpu: transformers + torch (CPU)
    - local-mlx: MLX (Apple Silicon)
    - local-cuda: transformers + torch (CUDA)
    - _Requirements: 12.2, 12.4, 12.5_
  - [x] 22.2.5 GPU依存の削除
    - CUDAを必須から選択可能に変更
    - Dockerfileからnvidia/cudaベースイメージを削除
    - docker-compose.ymlからGPU設定を削除
    - _Requirements: 12.1, 12.6_
  - [x] 22.2.6 環境設定とドキュメント更新
    - .envファイルにバックエンド設定を追加
    - README.mdにバックエンド選択ガイドを追加
    - DOCKER_GUIDE.mdを更新
    - _Requirements: 12.3, 12.8_
  - [x] 22.2.7 UIインポートエラーの修正
    - DockerfileにPYTHONPATH=/appを設定
    - UIコンテナでのインポートパス問題を解決
    - Streamlit起動確認
    - _Requirements: 3.1, 3.5_

## Phase 2.6: 包括的テスト実装とTDD体制構築

- [x] 22.3. テスト基盤のセットアップ
  - [x] 22.3.1 pytest設定の追加
    - pyproject.tomlにpytest設定を追加
    - カバレッジ設定（目標85%）
    - テストマーカー定義（unit、integration、e2e、slow）
    - _Testing Strategy: Coverage Configuration_
  - [x] 22.3.2 テスト依存関係の追加
    - pytest-cov（カバレッジ測定）
    - pytest-xdist（並列実行）
    - pytest-timeout（タイムアウト）
    - coverage[toml]（レポート生成）
    - uv.lockを更新
    - _Testing Strategy: Tools_
  - [x] 22.3.3 共通フィクスチャの実装
    - tests/conftest.pyを作成
    - chroma_client フィクスチャ（in-memory）
    - mock_llm_service フィクスチャ
    - mock_embedding_service フィクスチャ
    - sample_paper_metadata フィクスチャ
    - _Testing Strategy: Test Fixtures_
  - [x] 22.3.4 モックデータの作成
    - tests/fixtures/mock_responses.pyを作成
    - arXiv APIレスポンスのモック
    - Gemini APIレスポンスのモック
    - OpenAI APIレスポンスのモック
    - サンプルPDFテキスト
    - _Testing Strategy: Mocking Strategy_

- [-] 22.4. ユニットテスト実装（Phase 1: Critical Path）
  - [x] 22.4.1 LLMServiceのテスト
    - tests/unit/services/test_llm_service.pyを作成
    - バックエンド初期化テスト（全5バックエンド）
    - プロンプト構築テスト
    - 回答生成テスト（モック使用）
    - エラーハンドリングテスト
    - 目標カバレッジ: 90%+
    - _Requirements: 12.2, 12.3, 2.5_
  - [x] 22.4.2 EmbeddingServiceのテスト
    - tests/unit/services/test_embedding_service.pyを更新
    - バックエンド初期化テスト（全5バックエンド）
    - 単一テキストembeddingテスト
    - バッチembeddingテスト
    - エラーハンドリングテスト
    - 目標カバレッジ: 90%+
    - _Requirements: 12.2, 12.3, 2.2_
  - [x] 22.4.3 RAGServiceのテスト
    - tests/unit/services/test_rag_service.pyを更新
    - インデックス化テスト（モック使用）
    - IMRaD分割テスト
    - チャンク化テスト
    - 検索テスト（モック使用）
    - コンテキスト構築テスト
    - 目標カバレッジ: 90%+
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [x] 22.4.4 APIエンドポイントのテスト
    - tests/unit/api/test_endpoints.pyを作成
    - GET /health テスト
    - POST /papers/search テスト
    - POST /papers/download テスト
    - POST /rag/query テスト
    - エラーレスポンステスト（503、500、400）
    - 目標カバレッジ: 85%+
    - _Requirements: 9.1, 9.2, 9.3, 9.5_

- [x] 22.5. ユニットテスト実装（Phase 2: Service Layer）
  - [x] 22.5.1 PaperServiceのテスト
    - tests/unit/services/test_paper_service.pyを更新
    - 論文検索テスト（モック使用）
    - PDFダウンロードテスト（モック使用）
    - メタデータ取得テスト
    - キャッシュ動作テスト
    - 目標カバレッジ: 90%+
    - _Requirements: 1.1, 1.4, 1.5_
  - [x] 22.5.2 ChromaClientのテスト
    - tests/unit/clients/test_chroma_client.pyを作成
    - 初期化テスト
    - add()メソッドテスト
    - search()メソッドテスト
    - フィルタリングテスト
    - 目標カバレッジ: 85%+
    - _Requirements: 2.2, 2.3, 2.4_
  - [x] 22.5.3 ArxivClientのテスト
    - tests/unit/clients/test_arxiv_client.pyを作成
    - search_papers()テスト（モック使用）
    - get_metadata()テスト（モック使用）
    - download_pdf()テスト（モック使用）
    - エラーハンドリングテスト
    - 目標カバレッジ: 80%+
    - _Requirements: 1.1, 1.4_
  - [x] 22.5.4 データモデルのテスト
    - tests/unit/models/test_paper.pyを作成
    - tests/unit/models/test_rag.pyを作成
    - tests/unit/models/test_config.pyを作成
    - バリデーションテスト
    - シリアライゼーションテスト
    - 目標カバレッジ: 95%+
    - _Requirements: 1.5, 2.3_

- [x] 22.6. 統合テスト実装
  - [x] 22.6.1 RAGパイプライン統合テスト
    - tests/integration/test_rag_pipeline.pyを更新
    - 実際のChromaDB使用
    - LLM/Embeddingはモック
    - インデックス→検索→回答生成のフロー
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  - [x] 22.6.2 Chroma統合テスト
    - tests/integration/test_chroma_integration.pyを更新
    - 実際のChromaDB使用
    - 永続化テスト
    - 大量データテスト
    - _Requirements: 2.2, 2.3_
  - [x] 22.6.3 API統合テスト
    - tests/integration/test_api_integration.pyを作成
    - TestClientを使用
    - 実際のChromaDB使用
    - LLMはモック
    - エンドポイント間の連携テスト
    - _Requirements: 9.1, 9.2, 9.3_
  - [x] 22.6.4 マルチバックエンド統合テスト
    - tests/integration/test_multi_backend.pyを作成
    - 各バックエンドの切り替えテスト
    - 環境変数による設定テスト
    - _Requirements: 12.2, 12.3_

- [x] 22.7. E2Eテスト実装
  - [x] 22.7.1 論文ワークフローE2Eテスト
    - tests/e2e/test_paper_workflow.pyを作成
    - 検索→ダウンロード→インデックス→質問のフルフロー
    - 実際のAPIエンドポイント使用
    - LLMはモック（高速化）
    - _Requirements: 1.1, 1.4, 2.1, 2.2, 2.4, 2.5_
  - [x] 22.7.2 RAGワークフローE2Eテスト
    - tests/e2e/test_rag_workflow.pyを作成
    - 複数論文のインデックス化
    - 複数質問の実行
    - フィルタリング機能のテスト
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  - [x] 22.7.3 バックエンド切り替えE2Eテスト
    - tests/e2e/test_backend_switching.pyを作成
    - Gemini→OpenAI→local-cpuの切り替え
    - 各バックエンドでの基本動作確認
    - _Requirements: 12.2, 12.3, 12.8_

- [x] 22.8. カバレッジ測定と改善
  - [x] 22.8.1 初回カバレッジ測定
    - `uv run pytest --cov=src --cov-report=html`を実行
    - カバレッジレポートを確認
    - 未カバー箇所を特定
    - _Testing Strategy: Coverage Targets_
  - [x] 22.8.2 カバレッジ目標達成
    - Services: 90%+
    - API Endpoints: 85%+
    - Models: 95%+
    - Clients: 80%+
    - 全体: 85%+
    - 不足箇所のテスト追加
    - _Testing Strategy: Coverage Targets_
  - [x] 22.8.3 カバレッジレポートの統合
    - HTMLレポート生成
    - CI/CDでのカバレッジチェック
    - カバレッジバッジの追加（README.md）
    - _Testing Strategy: CI/CD Integration_

- [-] 22.9. CI/CD統合
  - [x] 22.9.1 GitHub Actions設定
    - .github/workflows/test.ymlを作成
    - ユニットテスト自動実行
    - 統合テスト自動実行
    - カバレッジアップロード（Codecov）
    - _Testing Strategy: CI/CD Integration_
  - [x] 22.9.2 pre-commit hooks設定
    - .pre-commit-config.yamlを作成
    - pytest実行（ユニットテストのみ）
    - カバレッジチェック
    - _Testing Strategy: TDD Workflow_

- [x] 22.10. ドキュメント更新
  - [x] 22.10.1 テスト実行ガイド作成
    - docs/TESTING.mdを作成
    - テスト実行方法
    - TDDワークフロー
    - トラブルシューティング
    - _Testing Strategy: Documentation_
  - [x] 22.10.2 README更新
    - テストセクションを追加
    - カバレッジバッジを追加
    - テストコマンドを追加
    - _Testing Strategy: Documentation_
  - [x] 22.10.3 開発ガイドライン更新
    - .kiro/steering/development-guidelines.mdを更新
    - TDD必須化
    - テストカバレッジ要件
    - テストレビューチェックリスト
    - _Testing Strategy: TDD Workflow_

## Phase 3: RAG強化

- [ ] 23. Support Score計算の実装
  - src/services/rag_service.pyにcalculate_support_score()関数を実装
  - LLMを使用して検索結果が質問に対して十分な情報を含むか評価（0-1スコア）
  - プロンプトエンジニアリング（日本語で評価指示）
  - _Requirements: 3.1_

- [ ] 24. HyDE（Hypothetical Document Embeddings）の実装
  - src/services/rag_service.pyにgenerate_hyde_query()関数を実装
  - LLMを使用して質問から仮想的な論文サマリーを生成
  - 生成されたサマリーをクエリとして使用
  - _Requirements: 4.2_

- [ ] 25. Corrective Retrievalの実装
  - src/services/rag_service.pyにcorrective_rag_query()関数を実装
  - Baseline検索→Support Score計算→必要に応じてHyDE再検索のフローを実装
  - support_threshold（デフォルト0.6）をパラメータ化
  - attempts回数をメタデータに記録
  - 両方失敗時の日本語No-answerメッセージ生成
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 26. SSEストリーミングの実装
  - src/api/streaming.pyにSSEレスポンス生成ユーティリティを実装
  - POST /rag/stream エンドポイントを実装
  - status、content（50-80文字チャンク）、doneフィールドを含むSSEイベントを送信
  - LLM生成をストリーミング対応に変更（generate_stream()メソッド）
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 27. Graceful Degradationの実装
  - src/services/rag_service.pyにgenerate_with_fallback()関数を実装
  - LLM失敗時にコンテキストの要約を返すフォールバック処理
  - エラーログ記録
  - _Requirements: 6.5_

- [ ] 28. Phase 3統合テスト
  - tests/integration/test_corrective_retrieval.pyを作成（Support Score、HyDE、再検索のテスト）
  - tests/integration/test_sse_streaming.pyを作成（SSEストリーミングのテスト）
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 8.1, 8.2, 8.3, 8.4_

## Phase 4: 高度な機能

- [ ] 29. LangGraph Message Routerの実装
  - src/agents/router.pyにRouterStateを定義（TypedDict）
  - classify_message()ノードを実装（メッセージプレフィックスで分類）
  - route_to_workflow()条件分岐関数を実装
  - StateGraphでルーターグラフを構築
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [ ] 30. 検索ワークフローエージェントの実装
  - src/agents/search_agent.pyにsearch_workflow()を実装
  - メッセージから検索クエリを抽出
  - PaperServiceで論文検索
  - 結果を構造化して返す
  - _Requirements: 5.2_

- [ ] 31. 比較分析エージェントの実装
  - src/agents/comparison_agent.pyにcompare_workflow()を実装
  - 複数のarxiv_idsから論文データを取得
  - LLMを使用して貢献、手法、データセットを比較
  - 日本語で構造化された比較レポートを生成
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ] 32. 背景知識収集エージェントの実装
  - src/agents/prereq_agent.pyにprereq_workflow()を実装
  - 論文から前提知識・背景知識を抽出
  - 関連する基礎概念をリストアップ
  - _Requirements: 5.3_

- [ ] 33. 引用ネットワークエージェントの実装
  - src/agents/network_agent.pyにnetwork_workflow()を実装
  - CrossRef APIとSemantic Scholar APIを統合
  - 引用関係を探索してネットワーク構造を構築
  - _Requirements: 5.4_

- [ ] 34. CrossRefとSemantic Scholar APIクライアントの実装
  - src/clients/crossref_client.pyにCrossRefClientクラスを実装
  - src/clients/semantic_client.pyにSemanticScholarClientクラスを実装
  - DOI解決、引用関係取得、メタデータ取得メソッドを実装
  - _Requirements: 1.2, 1.3_

- [ ] 35. Cornell Notes生成の実装
  - src/services/analysis_service.pyにAnalysisServiceクラスを実装
  - generate_cornell_notes()メソッドを実装（主要ポイント、詳細、要約の3セクション）
  - LLMプロンプトで日本語Cornell Notes形式を指示
  - _Requirements: 6.1, 6.2_

- [ ] 36. Quiz生成の実装
  - src/services/analysis_service.pyにgenerate_quiz()メソッドを実装
  - 論文内容から2-3問のQuizを生成
  - 各問題に正解と解説を含める
  - _Requirements: 6.3, 6.4_

- [ ] 37. Daily Digest生成の実装
  - src/services/digest_service.pyにDigestServiceクラスを実装
  - generate_digest()メソッドを実装（カテゴリ、日数、limitパラメータ）
  - NGキーワード・OKキーワードフィルタリングを実装
  - LLMで日本語要約を生成
  - DigestItemとして整形
  - 非同期Prefetch（PDF、セクション解析、フルテキスト）を実装
  - _Requirements: 7.1, 7.2_

- [ ] 38. Digest詳細表示の実装
  - POST /digest/details エンドポイントを実装
  - セクション構造解析を表示
  - 引用・メタデータを表示
  - Cornell Notes & Quizを生成して表示
  - キャッシュ済みフルテキストを表示
  - _Requirements: 7.2_

- [ ] 39. Router APIエンドポイントの実装
  - POST /router/query エンドポイントを実装
  - LangGraph router_graphを実行
  - ワークフロー名と結果を返す
  - SSE対応（オプション）
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 8.5_

- [ ] 40. 比較分析APIエンドポイントの実装
  - POST /papers/compare エンドポイントを実装
  - ComparisonAgentを使用
  - ComparisonResultを返す
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ] 41. Digest APIエンドポイントの実装
  - POST /digest/generate エンドポイントを実装
  - DigestServiceを使用
  - DigestItemのリストを返す
  - SSE対応（オプション）
  - _Requirements: 7.1, 7.2, 8.5_

- [ ] 42. Phase 4統合テスト
  - tests/integration/test_langgraph_router.pyを作成（Message Routerのテスト）
  - tests/integration/test_comparison_agent.pyを作成（比較分析のテスト）
  - tests/integration/test_digest.pyを作成（Digest生成のテスト）
  - tests/e2e/test_full_workflow.pyを作成（全ワークフローのE2Eテスト）
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2, 6.3, 6.4, 7.1, 7.2, 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ] 43. パフォーマンス最適化
  - Embedding生成のバッチ処理最適化
  - PDF処理の非同期化
  - LLMキャッシュの実装（同一質問の結果をキャッシュ）
  - Prefetchの並列処理最適化
  - GPU最適化（バッチサイズ調整、量子化検討）
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 44. 最終ドキュメント更新
  - README.mdに全Phase機能を追加
  - API仕様書を完全版に更新
  - アーキテクチャ図を追加
  - 使用例とサンプルクエリを充実
  - トラブルシューティングセクションを追加
  - _Requirements: 10.1, 10.2, 10.3, 10.4_
