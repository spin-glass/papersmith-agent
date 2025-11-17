"""arXiv API統合テスト

実際のarXiv APIを使用して、論文検索、メタデータ取得、PDF取得をテストします。

Requirements: 1.1, 1.4
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.clients.arxiv_client import ArxivClient
from src.services.paper_service import PaperService


@pytest.fixture
def temp_cache_dir():
    """一時的なキャッシュディレクトリを作成"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # クリーンアップ
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def arxiv_client(temp_cache_dir):
    """テスト用ArxivClientを作成"""
    return ArxivClient(
        cache_dir=temp_cache_dir / "pdfs",
        max_retries=3,
        timeout=30
    )


@pytest.fixture
def paper_service(arxiv_client, temp_cache_dir):
    """テスト用PaperServiceを作成"""
    return PaperService(
        arxiv_client=arxiv_client,
        cache_dir=temp_cache_dir
    )


@pytest.mark.asyncio
async def test_arxiv_search_papers(arxiv_client):
    """論文検索のテスト（実際のarXiv API使用）"""
    # 実際のarXiv APIで検索
    papers = await arxiv_client.search_papers(
        query="machine learning",
        max_results=5
    )
    
    # 結果が返されることを確認
    assert len(papers) > 0
    assert len(papers) <= 5
    
    # 各論文が必要な属性を持つことを確認
    for paper in papers:
        assert paper.arxiv_id
        assert paper.title
        assert len(paper.authors) > 0
        assert paper.abstract
        assert paper.year > 0
        assert len(paper.categories) > 0
        assert paper.pdf_url
        assert paper.published_date


@pytest.mark.asyncio
async def test_arxiv_get_metadata(arxiv_client):
    """メタデータ取得のテスト（実際のarXiv API使用）"""
    # 実在する論文ID（arXivの最初の論文）
    arxiv_id = "0704.0001"
    
    # メタデータを取得
    paper = await arxiv_client.get_metadata(arxiv_id)
    
    # メタデータが正しく取得されることを確認
    assert paper.arxiv_id == arxiv_id
    assert paper.title
    assert len(paper.authors) > 0
    assert paper.abstract
    assert paper.year == 2007
    assert paper.pdf_url


@pytest.mark.asyncio
async def test_arxiv_download_pdf(arxiv_client, temp_cache_dir):
    """PDF取得のテスト（実際のarXiv API使用）"""
    # 実在する論文ID
    arxiv_id = "0704.0001"
    
    # PDFをダウンロード
    pdf_path = await arxiv_client.download_pdf(arxiv_id)
    
    # PDFファイルが存在することを確認
    assert pdf_path.exists()
    assert pdf_path.suffix == ".pdf"
    assert pdf_path.stat().st_size > 0
    
    # キャッシュディレクトリに保存されていることを確認
    assert str(temp_cache_dir) in str(pdf_path)


@pytest.mark.asyncio
async def test_arxiv_download_pdf_cached(arxiv_client):
    """PDFキャッシュのテスト"""
    arxiv_id = "0704.0001"
    
    # 1回目のダウンロード
    pdf_path1 = await arxiv_client.download_pdf(arxiv_id)
    assert pdf_path1.exists()
    
    # ファイルの更新時刻を記録
    mtime1 = pdf_path1.stat().st_mtime
    
    # 2回目のダウンロード（キャッシュが使用されるはず）
    pdf_path2 = await arxiv_client.download_pdf(arxiv_id)
    assert pdf_path2.exists()
    assert pdf_path1 == pdf_path2
    
    # ファイルが再ダウンロードされていないことを確認
    mtime2 = pdf_path2.stat().st_mtime
    assert mtime1 == mtime2


@pytest.mark.asyncio
async def test_paper_service_search(paper_service):
    """PaperService論文検索のテスト"""
    papers = await paper_service.search_papers(
        query="deep learning",
        max_results=3
    )
    
    assert len(papers) > 0
    assert len(papers) <= 3
    
    for paper in papers:
        assert paper.arxiv_id
        assert paper.title
        assert len(paper.authors) > 0


@pytest.mark.asyncio
async def test_paper_service_get_metadata(paper_service):
    """PaperServiceメタデータ取得のテスト"""
    arxiv_id = "0704.0001"
    
    # メタデータを取得
    paper = await paper_service.get_metadata(arxiv_id)
    
    assert paper.arxiv_id == arxiv_id
    assert paper.title
    assert len(paper.authors) > 0


@pytest.mark.asyncio
async def test_paper_service_metadata_cache(paper_service, temp_cache_dir):
    """PaperServiceメタデータキャッシュのテスト"""
    arxiv_id = "0704.0001"
    
    # 1回目の取得
    paper1 = await paper_service.get_metadata(arxiv_id)
    
    # キャッシュファイルが作成されていることを確認
    cache_file = temp_cache_dir / "metadata" / f"{arxiv_id}.json"
    assert cache_file.exists()
    
    # 2回目の取得（キャッシュから読み込まれるはず）
    paper2 = await paper_service.get_metadata(arxiv_id)
    
    # 同じデータが返されることを確認
    assert paper1.arxiv_id == paper2.arxiv_id
    assert paper1.title == paper2.title


@pytest.mark.asyncio
async def test_paper_service_download_and_extract(paper_service):
    """PaperService PDF取得とテキスト抽出のテスト"""
    arxiv_id = "0704.0001"
    
    # PDFをダウンロード
    pdf_path = await paper_service.download_pdf(arxiv_id)
    assert pdf_path.exists()
    
    # テキストを抽出
    text = await paper_service.extract_text(pdf_path)
    
    # テキストが抽出されることを確認
    assert len(text) > 0
    assert isinstance(text, str)
    
    # 論文らしい内容が含まれることを確認（簡易チェック）
    # PDFによっては特定のキーワードが含まれない場合があるため、最小限のチェックのみ
    text_lower = text.lower()
    # 少なくとも何らかの英数字が含まれていることを確認
    assert any(c.isalnum() for c in text)


@pytest.mark.asyncio
async def test_paper_service_full_workflow(paper_service):
    """PaperService完全ワークフローのテスト（検索→メタデータ→PDF→テキスト抽出）"""
    # 1. 論文検索
    papers = await paper_service.search_papers(
        query="neural networks",
        max_results=1
    )
    assert len(papers) > 0
    
    arxiv_id = papers[0].arxiv_id
    
    # 2. メタデータ取得
    metadata = await paper_service.get_metadata(arxiv_id)
    assert metadata.arxiv_id == arxiv_id
    
    # 3. PDF取得
    pdf_path = await paper_service.download_pdf(arxiv_id)
    assert pdf_path.exists()
    
    # 4. テキスト抽出
    text = await paper_service.extract_text(pdf_path)
    assert len(text) > 0
