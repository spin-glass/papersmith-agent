# Implementation Plan

このタスクリストは、Playwrightを使用したStreamlit UIのE2Eテストを段階的に実装するための具体的なコーディングタスクです。

## Phase 1: 基盤セットアップ

- [x] 1. Playwright環境のセットアップ
  - pyproject.tomlにPlaywright依存関係を追加（playwright、pytest-playwright）
  - uv.lockを更新（`uv lock`）
  - Playwrightブラウザをインストール（`uv run playwright install chromium`）
  - pytest設定をpyproject.tomlに追加（e2e、ui、slowマーカー）
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. テストディレクトリ構造の作成
  - tests/e2e/ディレクトリを作成
  - tests/e2e/pages/ディレクトリを作成（Page Objects用）
  - tests/e2e/utils/ディレクトリを作成（ユーティリティ関数用）
  - tests/e2e/fixtures/ディレクトリを作成（テストデータ用）
  - test-results/ディレクトリを作成（スクリーンショット・ビデオ保存用）
  - _Requirements: 1.1, 9.1_

- [x] 3. 共通Fixturesの実装
  - tests/e2e/conftest.pyを作成
  - fastapi_server fixtureを実装（FastAPI起動・停止）
  - streamlit_server fixtureを実装（Streamlit起動・停止）
  - page fixtureを実装（Playwrightページオブジェクト）
  - test_data fixtureを実装（モックデータ）
  - _Requirements: 1.5, 9.1, 9.2_

- [x] 4. サーバー管理ユーティリティの実装
  - tests/e2e/utils/server.pyを作成
  - wait_for_server()関数を実装（サーバー起動待機）
  - cleanup_test_data()関数を実装（テストデータクリーンアップ）
  - _Requirements: 1.5, 9.3_

- [x] 5. キャプチャユーティリティの実装
  - tests/e2e/utils/capture.pyを作成
  - capture_on_failure()関数を実装（スクリーンショット・ログ保存）
  - save_console_logs()関数を実装（ブラウザコンソールログ保存）
  - save_network_logs()関数を実装（ネットワークログ保存）
  - _Requirements: 8.3, 8.4, 10.1, 10.2, 10.3_

## Phase 2: Page Objectsの実装

- [x] 6. Base Page Objectの実装
  - tests/e2e/pages/base_page.pyを作成
  - BasePageクラスを実装
  - navigate()メソッドを実装（ページ遷移）
  - wait_for_load()メソッドを実装（読み込み待機）
  - take_screenshot()メソッドを実装（スクリーンショット撮影）
  - get_error_message()メソッドを実装（エラーメッセージ取得）
  - _Requirements: 2.1, 6.1, 10.1_

- [x] 7. Home Page Objectの実装
  - tests/e2e/pages/home_page.pyを作成
  - HomePageクラスを実装（BasePageを継承）
  - is_loaded()メソッドを実装（ページ読み込み確認）
  - get_navigation_links()メソッドを実装（ナビゲーションリンク取得）
  - navigate_to_search()メソッドを実装（検索ページへ遷移）
  - navigate_to_rag()メソッドを実装（RAGページへ遷移）
  - navigate_to_papers()メソッドを実装（論文一覧ページへ遷移）
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 8. Search Page Objectの実装
  - tests/e2e/pages/search_page.pyを作成
  - SearchPageクラスを実装（BasePageを継承）
  - search()メソッドを実装（論文検索）
  - get_results_count()メソッドを実装（検索結果数取得）
  - get_first_result_title()メソッドを実装（最初の結果タイトル取得）
  - download_first_result()メソッドを実装（最初の結果をダウンロード）
  - wait_for_search_complete()メソッドを実装（検索完了待機）
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 9. RAG Page Objectの実装
  - tests/e2e/pages/rag_page.pyを作成
  - RAGPageクラスを実装（BasePageを継承）
  - ask_question()メソッドを実装（質問送信）
  - get_answer()メソッドを実装（回答取得）
  - expand_sources()メソッドを実装（参照元展開）
  - get_source_chunks()メソッドを実装（参照元チャンク取得）
  - wait_for_answer_complete()メソッドを実装（回答生成完了待機）
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 10. Papers Page Objectの実装
  - tests/e2e/pages/papers_page.pyを作成
  - PapersPageクラスを実装（BasePageを継承）
  - get_papers_count()メソッドを実装（論文数取得）
  - get_paper_titles()メソッドを実装（論文タイトルリスト取得）
  - is_empty()メソッドを実装（空状態確認）
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

## Phase 3: 基本テストケースの実装

- [x] 11. Home Pageテストの実装
  - tests/e2e/test_home_page.pyを作成
  - test_home_page_loads()を実装（ページ読み込みテスト）
  - test_navigation_links_present()を実装（ナビゲーションリンクテスト）
  - test_page_load_performance()を実装（読み込み時間テスト）
  - test_title_display()を実装（タイトル表示テスト）
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 7.1_

- [x] 12. Search Pageテストの実装
  - tests/e2e/test_search_page.pyを作成
  - test_search_papers()を実装（論文検索テスト）
  - test_search_results_display()を実装（検索結果表示テスト）
  - test_download_paper()を実装（論文ダウンロードテスト）
  - test_search_error_handling()を実装（検索エラーハンドリングテスト）
  - test_empty_search()を実装（空検索テスト）
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 7.2_

- [x] 13. RAG Pageテストの実装
  - tests/e2e/test_rag_page.pyを作成
  - test_rag_query()を実装（RAG質問応答テスト）
  - test_rag_answer_display()を実装（回答表示テスト）
  - test_rag_sources_display()を実装（参照元表示テスト）
  - test_rag_empty_index_warning()を実装（空インデックス警告テスト）
  - test_rag_error_handling()を実装（RAGエラーハンドリングテスト）
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 7.3_

- [x] 14. Papers Pageテストの実装
  - tests/e2e/test_papers_page.pyを作成
  - test_papers_list_display()を実装（論文一覧表示テスト）
  - test_papers_metadata_display()を実装（論文メタデータ表示テスト）
  - test_papers_empty_state()を実装（空状態テスト）
  - test_papers_count_display()を実装（論文数表示テスト）
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 7.4_

## Phase 4: エラーハンドリングとパフォーマンステスト

- [ ] 15. エラーハンドリングテストの実装
  - tests/e2e/test_error_handling.pyを作成
  - test_api_connection_error()を実装（API接続エラーテスト）
  - test_503_error_handling()を実装（503エラーハンドリングテスト）
  - test_500_error_handling()を実装（500エラーハンドリングテスト）
  - test_400_error_handling()を実装（400エラーハンドリングテスト）
  - test_network_timeout()を実装（ネットワークタイムアウトテスト）
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 16. パフォーマンステストの実装
  - tests/e2e/test_performance.pyを作成
  - test_home_page_load_time()を実装（ホームページ読み込み時間テスト）
  - test_search_response_time()を実装（検索応答時間テスト）
  - test_rag_response_time()を実装（RAG応答時間テスト）
  - test_papers_list_load_time()を実装（論文一覧読み込み時間テスト）
  - test_page_transition_time()を実装（ページ遷移時間テスト）
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

## Phase 5: E2Eワークフローテスト

- [ ] 17. 論文検索→ダウンロード→RAGワークフローテストの実装
  - tests/e2e/test_full_workflow.pyを作成
  - test_search_download_rag_workflow()を実装（フルワークフローテスト）
  - 検索→ダウンロード→RAG質問の一連のフローをテスト
  - 各ステップでデータの整合性を確認
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3_

- [ ] 18. 複数論文ワークフローテストの実装
  - tests/e2e/test_multi_paper_workflow.pyを作成
  - test_multiple_papers_download()を実装（複数論文ダウンロードテスト）
  - test_multiple_papers_rag()を実装（複数論文RAGテスト）
  - 複数論文のダウンロードとRAG質問をテスト
  - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.2, 5.1, 5.2_

## Phase 6: CI/CD統合とドキュメント

- [ ] 19. GitHub Actionsワークフローの作成
  - .github/workflows/e2e-tests.ymlを作成
  - E2Eテスト自動実行ジョブを定義
  - Playwrightブラウザインストールステップを追加
  - テスト実行ステップを追加（headlessモード）
  - テスト結果アップロードステップを追加（失敗時のみ）
  - _Requirements: 8.1, 8.2, 8.6_

- [ ] 20. テスト失敗時のアーティファクト保存設定
  - GitHub Actionsでスクリーンショット保存を設定
  - GitHub Actionsでビデオ録画保存を設定
  - GitHub Actionsでコンソールログ保存を設定
  - アーティファクトの保持期間を設定（7日間）
  - _Requirements: 8.3, 8.4, 10.1, 10.2, 10.3_

- [ ] 21. テスト実行スクリプトの作成
  - scripts/run_e2e_tests.shを作成
  - サーバー起動→テスト実行→サーバー停止の自動化
  - headless/headedモードの切り替えオプション
  - slowモードの切り替えオプション
  - _Requirements: 1.4, 10.4, 10.5_

- [ ] 22. E2Eテストドキュメントの作成
  - docs/E2E_TESTING.mdを作成
  - テスト実行方法を記載
  - デバッグ方法を記載（headed、slowモード）
  - トラブルシューティングを記載
  - CI/CD統合方法を記載
  - _Requirements: 8.1, 8.2, 10.4, 10.5_

- [ ] 23. README.mdの更新
  - E2Eテストセクションを追加
  - テスト実行コマンドを追加
  - Playwrightセットアップ手順を追加
  - _Requirements: 8.1, 8.2_

## Phase 7: テストデータ管理とクリーンアップ

- [ ] 24. テストデータFixturesの実装
  - tests/e2e/fixtures/test_data.pyを作成
  - mock_papers_data()関数を実装（モック論文データ）
  - mock_search_results()関数を実装（モック検索結果）
  - mock_rag_response()関数を実装（モックRAG応答）
  - _Requirements: 9.1, 9.2_

- [ ] 25. テストデータクリーンアップの実装
  - tests/e2e/conftest.pyにクリーンアップロジックを追加
  - テスト実行前にテスト用データベースを初期化
  - テスト実行後にテスト用データをクリーンアップ
  - 各テストが独立して実行可能であることを確認
  - _Requirements: 9.2, 9.3, 9.4, 9.5_

## Phase 8: 最終検証とドキュメント完成

- [ ] 26. 全E2Eテストの実行と検証
  - 全テストをheadlessモードで実行
  - 全テストをheadedモードで実行（デバッグ確認）
  - 並列実行テスト（`pytest -n auto`）
  - CI環境でのテスト実行確認
  - _Requirements: 8.1, 8.2, 8.6_

- [ ] 27. テストカバレッジの確認
  - 全要件がテストでカバーされていることを確認
  - 各Page Objectが適切にテストされていることを確認
  - エラーケースが網羅されていることを確認
  - _Requirements: 2.1-2.5, 3.1-3.7, 4.1-4.7, 5.1-5.5, 6.1-6.5, 7.1-7.5_

- [ ] 28. ドキュメントの最終レビュー
  - docs/E2E_TESTING.mdの内容を確認
  - README.mdのE2Eテストセクションを確認
  - コード内のコメントを確認
  - _Requirements: 8.1, 8.2_

- [ ] 29. Phase2機能の動作確認
  - E2Eテストを実行してPhase2機能の動作を検証
  - 発見された問題をリストアップ
  - 問題の修正または別タスクとして記録
  - _Requirements: 2.1-2.5, 3.1-3.7, 4.1-4.7, 5.1-5.5_
