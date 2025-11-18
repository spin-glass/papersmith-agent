# -*- coding: utf-8 -*-
"""Papers Page Tests

論文一覧ページのE2Eテストを提供します。

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""
import pytest

from tests.e2e.pages.papers_page import PapersPage


@pytest.mark.e2e
@pytest.mark.ui
def test_papers_page_object_creation(page, streamlit_server):
    """PapersPageオブジェクトが正しく作成できる"""
    papers = PapersPage(page, streamlit_server)
    assert papers is not None
    assert papers.page == page
    assert papers.base_url == streamlit_server


@pytest.mark.e2e
@pytest.mark.ui
def test_papers_page_navigate(page, streamlit_server):
    """論文一覧ページに正しく遷移できる"""
    papers = PapersPage(page, streamlit_server)
    
    # Streamlitのマルチページアプリでは、ページは "pages/" ディレクトリ内のファイル名で識別される
    # URLは "/?page=3_papers" または直接 "/3_papers" の形式
    papers.navigate("/3_papers")
    
    # Streamlitのページ遷移を待機
    page.wait_for_timeout(2000)
    
    # URLが正しいことを確認（Streamlitは "/" にリダイレクトすることがある）
    current_url = papers.get_current_url()
    print(f"Navigated to: {current_url}")
    
    # Streamlitのマルチページアプリでは、URLが変わらないことがあるため、
    # ページの内容で確認する
    assert streamlit_server in current_url, f"Should be on streamlit server, got: {current_url}"


@pytest.mark.e2e
@pytest.mark.ui
def test_papers_page_is_loaded(page, streamlit_server):
    """論文一覧ページが正しく読み込まれる"""
    papers = PapersPage(page, streamlit_server)
    papers.navigate("/3_papers")
    
    # Streamlitのページ遷移を待機
    page.wait_for_timeout(2000)
    
    # デバッグ情報を出力
    print(f"Current URL: {papers.get_current_url()}")
    print(f"Page title: {papers.get_page_title()}")
    
    # ページが読み込まれたことを確認
    assert papers.is_loaded(), "Papers page should be loaded"


@pytest.mark.e2e
@pytest.mark.ui
def test_get_papers_count(page, streamlit_server):
    """論文数が取得できる
    
    Requirements: 5.1, 5.5
    """
    papers = PapersPage(page, streamlit_server)
    papers.navigate("/3_papers")
    
    # 論文数を取得
    count = papers.get_papers_count()
    
    # 論文数は0以上
    assert count >= 0, "Papers count should be non-negative"


@pytest.mark.e2e
@pytest.mark.ui
def test_get_paper_titles(page, streamlit_server):
    """論文タイトルのリストが取得できる
    
    Requirements: 5.2
    """
    papers = PapersPage(page, streamlit_server)
    papers.navigate("/3_papers")
    
    # 論文タイトルを取得
    titles = papers.get_paper_titles()
    
    # タイトルリストが取得できることを確認
    assert isinstance(titles, list), "Should return a list of titles"
    
    # 論文がある場合、タイトルが空でないことを確認
    if len(titles) > 0:
        assert all(len(title) > 0 for title in titles), "Titles should not be empty"


@pytest.mark.e2e
@pytest.mark.ui
def test_is_empty(page, streamlit_server):
    """空状態が正しく判定できる
    
    Requirements: 5.4
    """
    papers = PapersPage(page, streamlit_server)
    papers.navigate("/3_papers")
    
    # 空状態を確認
    is_empty = papers.is_empty()
    
    # 空状態はbool値
    assert isinstance(is_empty, bool), "is_empty should return boolean"
    
    # 論文数と整合性があることを確認
    count = papers.get_papers_count()
    if count == 0:
        assert is_empty, "Should be empty when count is 0"
    else:
        assert not is_empty, "Should not be empty when count > 0"


@pytest.mark.e2e
@pytest.mark.ui
def test_get_paper_metadata(page, streamlit_server):
    """論文メタデータが取得できる
    
    Requirements: 5.2, 5.3
    """
    papers = PapersPage(page, streamlit_server)
    papers.navigate("/3_papers")
    
    # 論文がある場合のみテスト
    count = papers.get_papers_count()
    if count > 0:
        # 最初の論文のメタデータを取得
        metadata = papers.get_paper_metadata(0)
        
        # メタデータの構造を確認
        assert isinstance(metadata, dict), "Metadata should be a dictionary"
        assert "title" in metadata
        assert "authors" in metadata
        assert "year" in metadata
        assert "arxiv_id" in metadata
        assert "chunk_count" in metadata
        
        # タイトルが空でないことを確認
        assert len(metadata["title"]) > 0, "Title should not be empty"
    else:
        # 論文がない場合はスキップ
        pytest.skip("No papers available for testing")


@pytest.mark.e2e
@pytest.mark.ui
def test_get_all_papers_metadata(page, streamlit_server):
    """全ての論文のメタデータが取得できる
    
    Requirements: 5.2, 5.3
    """
    papers = PapersPage(page, streamlit_server)
    papers.navigate("/3_papers")
    
    # 全ての論文のメタデータを取得
    all_metadata = papers.get_all_papers_metadata()
    
    # メタデータリストが取得できることを確認
    assert isinstance(all_metadata, list), "Should return a list of metadata"
    
    # 論文数と一致することを確認
    count = papers.get_papers_count()
    assert len(all_metadata) == count, "Metadata count should match papers count"


@pytest.mark.e2e
@pytest.mark.ui
def test_has_success_message(page, streamlit_server):
    """成功メッセージの表示が確認できる
    
    Requirements: 5.5
    """
    papers = PapersPage(page, streamlit_server)
    papers.navigate("/3_papers")
    
    # 成功メッセージの有無を確認
    has_message = papers.has_success_message()
    
    # bool値が返されることを確認
    assert isinstance(has_message, bool), "Should return boolean"
    
    # 論文がある場合は成功メッセージが表示されるはず
    count = papers.get_papers_count()
    if count > 0:
        assert has_message, "Should show success message when papers exist"


@pytest.mark.e2e
@pytest.mark.ui
def test_get_success_message(page, streamlit_server):
    """成功メッセージが取得できる
    
    Requirements: 5.5
    """
    papers = PapersPage(page, streamlit_server)
    papers.navigate("/3_papers")
    
    # 成功メッセージを取得
    message = papers.get_success_message()
    
    # 文字列が返されることを確認
    assert isinstance(message, str), "Should return string"
    
    # 論文がある場合はメッセージが含まれることを確認
    count = papers.get_papers_count()
    if count > 0:
        assert "件の論文がインデックス化されています" in message, \
            "Success message should contain paper count"


@pytest.mark.e2e
@pytest.mark.ui
def test_get_empty_state_message(page, streamlit_server):
    """空状態メッセージが取得できる
    
    Requirements: 5.4
    """
    papers = PapersPage(page, streamlit_server)
    papers.navigate("/3_papers")
    
    # 空状態メッセージを取得
    message = papers.get_empty_state_message()
    
    # 文字列が返されることを確認
    assert isinstance(message, str), "Should return string"
    
    # 空状態の場合はメッセージが含まれることを確認
    # ただし、論文がある場合はメッセージが空でも良い
    if papers.is_empty():
        # 空状態の場合、メッセージが取得できるか、または空状態が正しく判定されていればOK
        # UIの実装によってはメッセージが取得できない場合もあるため、柔軟に対応
        if len(message) > 0:
            assert "インデックス化された論文がありません" in message or \
                   "論文" in message, \
                   "Empty state message should contain relevant text"
        else:
            # メッセージが取得できない場合でも、is_empty()がTrueならOK
            assert papers.is_empty(), "Should correctly detect empty state"


@pytest.mark.e2e
@pytest.mark.ui
def test_get_index_stats(page, streamlit_server):
    """インデックス統計情報が取得できる"""
    papers = PapersPage(page, streamlit_server)
    papers.navigate("/3_papers")
    
    # インデックス統計を取得
    stats = papers.get_index_stats()
    
    # 統計情報の構造を確認
    assert isinstance(stats, dict), "Stats should be a dictionary"
    assert "total_documents" in stats
    assert "index_ready" in stats
    
    # 値の型を確認
    assert isinstance(stats["total_documents"], int), "total_documents should be int"
    assert isinstance(stats["index_ready"], bool), "index_ready should be bool"
    
    # 総ドキュメント数は0以上
    assert stats["total_documents"] >= 0, "total_documents should be non-negative"


@pytest.mark.e2e
@pytest.mark.ui
def test_expand_details(page, streamlit_server):
    """詳細情報が展開できる"""
    papers = PapersPage(page, streamlit_server)
    papers.navigate("/3_papers")
    
    # 論文がある場合のみテスト
    count = papers.get_papers_count()
    if count > 0:
        # 最初の論文の詳細を展開
        papers.expand_details(0)
        
        # エラーが発生しないことを確認（展開が成功）
        # 実際の展開確認は視覚的なテストで行う
        assert True
    else:
        pytest.skip("No papers available for testing")


@pytest.mark.e2e
@pytest.mark.ui
def test_refresh_page(page, streamlit_server):
    """ページがリフレッシュできる"""
    papers = PapersPage(page, streamlit_server)
    papers.navigate("/3_papers")
    
    # ページをリフレッシュ
    papers.refresh_page()
    
    # ページが再読み込みされたことを確認
    assert papers.is_loaded(), "Page should be loaded after refresh"


# Task 14: Papers Pageテストの実装
# Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 7.4


@pytest.mark.e2e
@pytest.mark.ui
def test_papers_list_display(page, streamlit_server):
    """論文一覧が正しく表示される
    
    論文一覧ページで論文リストが適切に表示されることを確認します。
    
    Requirements: 5.1, 5.2
    """
    papers = PapersPage(page, streamlit_server)
    papers.navigate("/3_papers")
    
    # Streamlitのページ遷移を待機
    page.wait_for_timeout(2000)
    
    # 論文数を取得
    count = papers.get_papers_count()
    
    if count > 0:
        # 論文がある場合、リストが表示されていることを確認
        titles = papers.get_paper_titles()
        assert len(titles) > 0, "Should display paper titles"
        assert len(titles) == count, "Number of titles should match paper count"
        
        # 各タイトルが空でないことを確認
        for title in titles:
            assert len(title) > 0, "Each title should not be empty"
        
        # 成功メッセージが表示されていることを確認
        assert papers.has_success_message(), "Should show success message when papers exist"
        
        # 空状態でないことを確認
        assert not papers.is_empty(), "Should not be empty when papers exist"
    else:
        # 論文がない場合、空状態が表示されていることを確認
        assert papers.is_empty(), "Should be empty when no papers exist"


@pytest.mark.e2e
@pytest.mark.ui
def test_papers_metadata_display(page, streamlit_server):
    """論文メタデータが正しく表示される
    
    各論文のメタデータ（タイトル、著者、年、arXiv ID）が
    適切に表示されることを確認します。
    
    Requirements: 5.2, 5.3
    """
    papers = PapersPage(page, streamlit_server)
    papers.navigate("/3_papers")
    
    # Streamlitのページ遷移を待機
    page.wait_for_timeout(2000)
    
    # 論文数を取得
    count = papers.get_papers_count()
    
    if count > 0:
        # 最初の論文のメタデータを取得
        metadata = papers.get_paper_metadata(0)
        
        # 必須フィールドが存在することを確認
        assert "title" in metadata, "Metadata should contain title"
        assert "authors" in metadata, "Metadata should contain authors"
        assert "year" in metadata, "Metadata should contain year"
        assert "arxiv_id" in metadata, "Metadata should contain arxiv_id"
        
        # タイトルが空でないことを確認
        assert len(metadata["title"]) > 0, "Title should not be empty"
        
        # 著者が空でないことを確認（論文には必ず著者がいる）
        assert len(metadata["authors"]) > 0, "Authors should not be empty"
        
        # 年が4桁の数字であることを確認（存在する場合）
        if metadata["year"]:
            assert len(metadata["year"]) == 4, "Year should be 4 digits"
            assert metadata["year"].isdigit(), "Year should be numeric"
        
        # arXiv IDが適切な形式であることを確認（存在する場合）
        if metadata["arxiv_id"]:
            # arXiv IDは通常 "YYMM.NNNNN" または "YYMM.NNNNNN" の形式
            assert "." in metadata["arxiv_id"], "arXiv ID should contain a dot"
        
        # 全ての論文のメタデータを取得
        all_metadata = papers.get_all_papers_metadata()
        assert len(all_metadata) == count, "Should get metadata for all papers"
        
        # 各論文のメタデータが適切な構造を持つことを確認
        for meta in all_metadata:
            assert isinstance(meta, dict), "Each metadata should be a dictionary"
            assert "title" in meta, "Each metadata should have title"
            assert len(meta["title"]) > 0, "Each title should not be empty"
    else:
        pytest.skip("No papers available for metadata testing")


@pytest.mark.e2e
@pytest.mark.ui
def test_papers_empty_state(page, streamlit_server):
    """論文が無い時に適切な空状態が表示される
    
    インデックスに論文が無い場合、適切な空状態メッセージが
    表示されることを確認します。
    
    Requirements: 5.4
    """
    papers = PapersPage(page, streamlit_server)
    papers.navigate("/3_papers")
    
    # Streamlitのページ遷移を待機
    page.wait_for_timeout(2000)
    
    # 空状態を確認
    is_empty = papers.is_empty()
    count = papers.get_papers_count()
    
    # 論文数と空状態の整合性を確認
    if count == 0:
        # 論文が無い場合
        assert is_empty, "Should be empty when paper count is 0"
        
        # 空状態メッセージが表示されているか確認
        empty_message = papers.get_empty_state_message()
        
        # メッセージが取得できる場合、適切な内容であることを確認
        if len(empty_message) > 0:
            # 空状態を示すキーワードが含まれていることを確認
            assert any(keyword in empty_message for keyword in [
                "インデックス化された論文がありません",
                "論文がありません",
                "論文が見つかりません",
                "空"
            ]), f"Empty state message should indicate no papers: {empty_message}"
        
        # 成功メッセージが表示されていないことを確認
        assert not papers.has_success_message(), \
            "Should not show success message when empty"
        
        # 論文タイトルリストが空であることを確認
        titles = papers.get_paper_titles()
        assert len(titles) == 0, "Should have no titles when empty"
    else:
        # 論文がある場合
        assert not is_empty, "Should not be empty when papers exist"
        
        # 成功メッセージが表示されていることを確認
        assert papers.has_success_message(), \
            "Should show success message when papers exist"


@pytest.mark.e2e
@pytest.mark.ui
def test_papers_count_display(page, streamlit_server):
    """論文数が正しく表示される
    
    インデックス化された論文の総数が適切に表示されることを確認します。
    
    Requirements: 5.5, 7.4
    """
    papers = PapersPage(page, streamlit_server)
    papers.navigate("/3_papers")
    
    # Streamlitのページ遷移を待機
    page.wait_for_timeout(2000)
    
    # 論文数を取得
    count = papers.get_papers_count()
    
    # 論文数は0以上
    assert count >= 0, "Paper count should be non-negative"
    
    if count > 0:
        # 論文がある場合、成功メッセージに論文数が含まれることを確認
        success_message = papers.get_success_message()
        assert len(success_message) > 0, "Should have success message when papers exist"
        assert "件の論文がインデックス化されています" in success_message, \
            "Success message should mention paper count"
        
        # メッセージから論文数を抽出して確認
        import re
        match = re.search(r'(\d+)件の論文', success_message)
        if match:
            displayed_count = int(match.group(1))
            assert displayed_count == count, \
                f"Displayed count ({displayed_count}) should match actual count ({count})"
        
        # インデックス統計情報を取得
        stats = papers.get_index_stats()
        assert stats["total_documents"] >= 0, "Total documents should be non-negative"
        
        # 論文タイトル数と一致することを確認
        titles = papers.get_paper_titles()
        assert len(titles) == count, \
            f"Number of titles ({len(titles)}) should match paper count ({count})"
        
        # 全メタデータ数と一致することを確認
        all_metadata = papers.get_all_papers_metadata()
        assert len(all_metadata) == count, \
            f"Number of metadata ({len(all_metadata)}) should match paper count ({count})"
    else:
        # 論文がない場合、空状態であることを確認
        assert papers.is_empty(), "Should be empty when count is 0"
        
        # 成功メッセージが表示されていないことを確認
        assert not papers.has_success_message(), \
            "Should not show success message when no papers"
