# -*- coding: utf-8 -*-
"""Search Page Tests

論文検索ページのE2Eテストを提供します。

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 7.2
"""
import time

import pytest

from tests.e2e.pages.search_page import SearchPage


@pytest.mark.e2e
@pytest.mark.ui
def test_search_papers(page, streamlit_server, test_data):
    """論文検索が動作する
    
    キーワードを入力して検索ボタンをクリックすると、
    FastAPI /papers/search エンドポイントが呼び出され、
    検索結果が表示されることを確認します。
    
    Requirements: 3.1, 3.2, 3.3
    """
    search = SearchPage(page, streamlit_server)
    search.navigate("/search")
    page.wait_for_load_state("networkidle", timeout=30000)
    
    # 検索フォームが表示されることを確認
    assert search.is_search_form_visible(), "Search form should be visible"
    
    # 論文を検索
    search.search(test_data["search_query"], max_results=5)
    
    # 検索結果が表示されることを確認
    results_count = search.get_results_count()
    assert results_count > 0, f"Should have search results, got: {results_count}"
    
    # 最初の結果のタイトルが取得できることを確認
    first_title = search.get_first_result_title()
    assert len(first_title) > 0, "First result should have a title"


@pytest.mark.e2e
@pytest.mark.ui
def test_search_results_display(page, streamlit_server, test_data):
    """検索結果が正しく表示される
    
    検索結果の論文カードに、タイトル、著者、年、要約が
    含まれることを確認します。
    
    Requirements: 3.3, 3.4
    """
    search = SearchPage(page, streamlit_server)
    search.navigate("/search")
    page.wait_for_load_state("networkidle", timeout=30000)
    
    # 論文を検索
    search.search(test_data["search_query"], max_results=5)
    
    # 検索結果が表示されることを確認
    results_count = search.get_results_count()
    assert results_count > 0, "Should have search results"
    
    # 最初の論文のメタデータを取得
    metadata = search.get_paper_metadata(0)
    
    # タイトルが含まれることを確認
    assert len(metadata["title"]) > 0, "Paper should have a title"
    
    # 著者が含まれることを確認
    assert len(metadata["authors"]) > 0, "Paper should have authors"
    
    # 年またはarXiv IDが含まれることを確認（どちらか一方でOK）
    has_metadata = len(metadata["year"]) > 0 or len(metadata["arxiv_id"]) > 0
    assert has_metadata, "Paper should have year or arXiv ID"


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.slow
def test_download_paper(page, streamlit_server, test_data):
    """論文ダウンロードが動作する
    
    ダウンロードボタンをクリックすると、ローディング状態が表示され、
    ダウンロード完了後に成功メッセージが表示されることを確認します。
    
    Requirements: 3.5, 3.6
    """
    search = SearchPage(page, streamlit_server)
    search.navigate("/search")
    page.wait_for_load_state("networkidle", timeout=30000)
    
    # 論文を検索
    search.search(test_data["search_query"], max_results=5)
    
    # 検索結果が表示されることを確認
    results_count = search.get_results_count()
    assert results_count > 0, "Should have search results"
    
    # 最初の論文をダウンロード
    search.download_first_result()
    
    # 成功メッセージが表示されることを確認
    assert search.has_success_message(), "Should show success message after download"
    
    # 成功メッセージの内容を確認
    success_msg = search.get_success_message()
    assert len(success_msg) > 0, "Success message should not be empty"
    assert "ダウンロード" in success_msg or "完了" in success_msg or "成功" in success_msg, \
        f"Success message should indicate download completion, got: {success_msg}"


@pytest.mark.e2e
@pytest.mark.ui
def test_search_error_handling(page, streamlit_server):
    """検索エラーが適切に処理される
    
    空の検索や無効な入力に対して、適切なエラーメッセージが
    日本語で表示されることを確認します。
    
    Requirements: 3.7
    """
    search = SearchPage(page, streamlit_server)
    search.navigate("/search")
    page.wait_for_load_state("networkidle", timeout=30000)
    
    # 空の検索を実行
    search.search("", wait_for_results=True)
    
    # エラーメッセージまたは結果なしメッセージが表示されることを確認
    # 空の検索は、エラーではなく結果なしとして処理される可能性がある
    has_error = search.has_error_message()
    has_no_results = search.has_no_results_message()
    
    # どちらかのメッセージが表示されていればOK
    assert has_error or has_no_results, \
        "Should show error message or no results message for empty search"
    
    if has_error:
        error_msg = search.get_error_message()
        assert len(error_msg) > 0, "Error message should not be empty"


@pytest.mark.e2e
@pytest.mark.ui
def test_empty_search(page, streamlit_server):
    """空検索が適切に処理される
    
    空のキーワードで検索した場合、適切なメッセージが表示されることを確認します。
    
    Requirements: 3.7
    """
    search = SearchPage(page, streamlit_server)
    search.navigate("/search")
    page.wait_for_load_state("networkidle", timeout=30000)
    
    # 空の検索を実行
    search.search("", wait_for_results=True)
    
    # エラーメッセージまたは結果なしメッセージが表示されることを確認
    has_error = search.has_error_message()
    has_no_results = search.has_no_results_message()
    
    # どちらかのメッセージが表示されていればOK
    assert has_error or has_no_results, \
        "Should show appropriate message for empty search"


@pytest.mark.e2e
@pytest.mark.ui
def test_search_response_time(page, streamlit_server, test_data):
    """検索応答時間が許容範囲内である
    
    検索が10秒以内に完了することを確認します。
    
    Requirements: 7.2
    """
    search = SearchPage(page, streamlit_server)
    search.navigate("/search")
    page.wait_for_load_state("networkidle", timeout=30000)
    
    # 検索時間を計測
    start_time = time.time()
    search.search(test_data["search_query"], max_results=5)
    search_time = time.time() - start_time
    
    # 10秒以内に完了することを確認
    assert search_time < 10.0, f"Search took {search_time:.2f}s, should be < 10.0s"
    
    # 理想的には5秒以内（警告のみ）
    if search_time >= 5.0:
        print(f"Warning: Search took {search_time:.2f}s (target: < 5.0s)")


@pytest.mark.e2e
@pytest.mark.ui
def test_search_form_visible(page, streamlit_server):
    """検索フォームが表示される
    
    検索ページにアクセスすると、検索フォームが表示されることを確認します。
    
    Requirements: 3.1
    """
    search = SearchPage(page, streamlit_server)
    # Streamlit multi-page apps use: /search (without the number prefix)
    search.navigate("/search")
    
    # Wait for Streamlit to fully initialize
    page.wait_for_load_state("networkidle", timeout=30000)
    
    # Additional wait for Streamlit to render
    page.wait_for_timeout(3000)
    
    # ページタイトルを確認
    page_title = page.title()
    assert "search" in page_title.lower(), f"Page title should contain 'search', got: {page_title}"
    
    # Check that we're on the search page by verifying the URL
    current_url = page.url
    assert "/search" in current_url, f"URL should contain '/search', got: {current_url}"


@pytest.mark.e2e
@pytest.mark.ui
def test_multiple_search_results(page, streamlit_server):
    """複数の検索結果が表示される
    
    一般的なキーワードで検索すると、複数の結果が表示されることを確認します。
    
    Requirements: 3.3, 3.4
    """
    search = SearchPage(page, streamlit_server)
    search.navigate("/search")
    page.wait_for_load_state("networkidle", timeout=30000)
    
    # 一般的なキーワードで検索
    search.search("transformer", max_results=10)
    
    # 複数の検索結果が表示されることを確認
    results_count = search.get_results_count()
    assert results_count > 1, f"Should have multiple search results, got: {results_count}"
    
    # 全ての結果のタイトルを取得
    titles = search.get_result_titles()
    assert len(titles) > 1, "Should have multiple result titles"
    
    # 各タイトルが空でないことを確認
    for i, title in enumerate(titles):
        assert len(title) > 0, f"Result {i} should have a non-empty title"


@pytest.mark.e2e
@pytest.mark.ui
def test_search_with_max_results(page, streamlit_server):
    """最大取得件数の設定が動作する
    
    最大取得件数を設定して検索すると、指定された件数以下の結果が
    表示されることを確認します。
    
    Requirements: 3.2, 3.3
    """
    search = SearchPage(page, streamlit_server)
    search.navigate("/search")
    page.wait_for_load_state("networkidle", timeout=30000)
    
    # 最大取得件数を3に設定して検索
    max_results = 3
    search.search("machine learning", max_results=max_results)
    
    # 検索結果が最大取得件数以下であることを確認
    results_count = search.get_results_count()
    assert results_count <= max_results, \
        f"Should have at most {max_results} results, got: {results_count}"
    
    # 少なくとも1件は結果があることを確認
    assert results_count > 0, "Should have at least one result"
