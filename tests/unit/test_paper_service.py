"""PaperServiceのユニットテスト

Requirements: 1.1, 1.4, 1.5
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.clients.arxiv_client import ArxivClient, ArxivClientError
from src.models.paper import PaperMetadata
from src.services.paper_service import PaperService, PaperServiceError


@pytest.fixture
def mock_arxiv_client():
    """モックArxivClient"""
    client = Mock(spec=ArxivClient)
    return client


@pytest.fixture
def paper_service(mock_arxiv_client, tmp_path):
    """PaperServiceインスタンス"""
    return PaperService(
        arxiv_client=mock_arxiv_client,
        cache_dir=tmp_path / "cache"
    )


@pytest.fixture
def sample_paper_metadata():
    """サンプル論文メタデータ"""
    return PaperMetadata(
        arxiv_id="2301.00001",
        title="Test Paper",
        authors=["Author One", "Author Two"],
        abstract="This is a test abstract.",
        year=2023,
        categories=["cs.AI"],
        pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
        published_date=datetime(2023, 1, 1)
    )


# ========================================
# search_papers tests
# ========================================

@pytest.mark.asyncio
async def test_search_papers_success(paper_service, mock_arxiv_client, sample_paper_metadata):
    """論文検索が成功する"""
    # モックの設定
    mock_arxiv_client.search_papers = AsyncMock(return_value=[sample_paper_metadata])

    # 実行
    results = await paper_service.search_papers("machine learning", max_results=10)

    # 検証
    assert len(results) == 1
    assert results[0].arxiv_id == "2301.00001"
    assert results[0].title == "Test Paper"
    mock_arxiv_client.search_papers.assert_called_once_with("machine learning", 10)


@pytest.mark.asyncio
async def test_search_papers_empty_results(paper_service, mock_arxiv_client):
    """論文検索で結果が0件"""
    # モックの設定
    mock_arxiv_client.search_papers = AsyncMock(return_value=[])

    # 実行
    results = await paper_service.search_papers("nonexistent query")

    # 検証
    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_papers_arxiv_error(paper_service, mock_arxiv_client):
    """論文検索でArxivClientErrorが発生"""
    # モックの設定
    mock_arxiv_client.search_papers = AsyncMock(
        side_effect=ArxivClientError("API error")
    )

    # 実行と検証
    with pytest.raises(PaperServiceError, match="Failed to search papers"):
        await paper_service.search_papers("test query")


@pytest.mark.asyncio
async def test_search_papers_unexpected_error(paper_service, mock_arxiv_client):
    """論文検索で予期しないエラーが発生"""
    # モックの設定
    mock_arxiv_client.search_papers = AsyncMock(
        side_effect=RuntimeError("Unexpected error")
    )

    # 実行と検証
    with pytest.raises(PaperServiceError, match="Unexpected error"):
        await paper_service.search_papers("test query")


# ========================================
# download_pdf tests
# ========================================

@pytest.mark.asyncio
async def test_download_pdf_success(paper_service, mock_arxiv_client, tmp_path):
    """PDFダウンロードが成功する"""
    # モックの設定
    downloaded_path = tmp_path / "downloaded.pdf"
    downloaded_path.write_bytes(b"PDF content")
    mock_arxiv_client.download_pdf = AsyncMock(return_value=downloaded_path)

    # 実行
    result_path = await paper_service.download_pdf("2301.00001")

    # 検証
    assert result_path.exists()
    assert result_path.name == "2301.00001.pdf"
    mock_arxiv_client.download_pdf.assert_called_once()


@pytest.mark.asyncio
async def test_download_pdf_with_url(paper_service, mock_arxiv_client, tmp_path):
    """PDF URLを指定してダウンロード"""
    # モックの設定
    downloaded_path = tmp_path / "downloaded.pdf"
    downloaded_path.write_bytes(b"PDF content")
    mock_arxiv_client.download_pdf = AsyncMock(return_value=downloaded_path)

    # 実行
    pdf_url = "https://arxiv.org/pdf/2301.00001.pdf"
    result_path = await paper_service.download_pdf("2301.00001", pdf_url=pdf_url)

    # 検証
    assert result_path.exists()
    mock_arxiv_client.download_pdf.assert_called_once_with("2301.00001", pdf_url)


@pytest.mark.asyncio
async def test_download_pdf_cached(paper_service, mock_arxiv_client, tmp_path):
    """キャッシュ済みPDFは再ダウンロードしない"""
    # キャッシュファイルを作成
    cache_dir = tmp_path / "cache" / "pdfs"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached_pdf = cache_dir / "2301.00001.pdf"
    cached_pdf.write_bytes(b"Cached PDF content")

    # 実行
    result_path = await paper_service.download_pdf("2301.00001")

    # 検証
    assert result_path == cached_pdf
    assert result_path.read_bytes() == b"Cached PDF content"
    # ArxivClientは呼ばれない
    mock_arxiv_client.download_pdf.assert_not_called()


@pytest.mark.asyncio
async def test_download_pdf_arxiv_error(paper_service, mock_arxiv_client):
    """PDFダウンロードでArxivClientErrorが発生"""
    # モックの設定
    mock_arxiv_client.download_pdf = AsyncMock(
        side_effect=ArxivClientError("Download failed")
    )

    # 実行と検証
    with pytest.raises(PaperServiceError, match="Failed to download PDF"):
        await paper_service.download_pdf("2301.00001")


@pytest.mark.asyncio
async def test_download_pdf_unexpected_error(paper_service, mock_arxiv_client):
    """PDFダウンロードで予期しないエラーが発生"""
    # モックの設定
    mock_arxiv_client.download_pdf = AsyncMock(
        side_effect=RuntimeError("Unexpected error")
    )

    # 実行と検証
    with pytest.raises(PaperServiceError, match="Unexpected error"):
        await paper_service.download_pdf("2301.00001")


# ========================================
# get_metadata tests
# ========================================

@pytest.mark.asyncio
async def test_get_metadata_from_cache(paper_service, sample_paper_metadata, tmp_path):
    """キャッシュからメタデータを取得"""
    # キャッシュファイルを作成
    cache_dir = tmp_path / "cache" / "metadata"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / "2301.00001.json"

    with open(cache_file, 'w', encoding='utf-8') as f:
        data = sample_paper_metadata.model_dump()
        data['published_date'] = sample_paper_metadata.published_date.isoformat()
        json.dump(data, f)

    # 実行
    result = await paper_service.get_metadata("2301.00001")

    # 検証
    assert result.arxiv_id == "2301.00001"
    assert result.title == "Test Paper"
    assert result.authors == ["Author One", "Author Two"]


@pytest.mark.asyncio
async def test_get_metadata_from_api(paper_service, mock_arxiv_client, sample_paper_metadata, tmp_path):
    """APIからメタデータを取得してキャッシュ"""
    # モックの設定
    mock_arxiv_client.get_metadata = AsyncMock(return_value=sample_paper_metadata)

    # 実行
    result = await paper_service.get_metadata("2301.00001")

    # 検証
    assert result.arxiv_id == "2301.00001"
    assert result.title == "Test Paper"
    mock_arxiv_client.get_metadata.assert_called_once_with("2301.00001")

    # キャッシュファイルが作成されたことを確認
    cache_file = tmp_path / "cache" / "metadata" / "2301.00001.json"
    assert cache_file.exists()

    # キャッシュ内容を確認
    with open(cache_file, encoding='utf-8') as f:
        cached_data = json.load(f)
        assert cached_data['arxiv_id'] == "2301.00001"
        assert cached_data['title'] == "Test Paper"


@pytest.mark.asyncio
async def test_get_metadata_force_refresh(paper_service, mock_arxiv_client, sample_paper_metadata, tmp_path):
    """force_refreshでキャッシュを無視してAPIから取得"""
    # キャッシュファイルを作成
    cache_dir = tmp_path / "cache" / "metadata"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / "2301.00001.json"

    old_metadata = sample_paper_metadata.model_copy()
    old_metadata.title = "Old Title"
    with open(cache_file, 'w', encoding='utf-8') as f:
        data = old_metadata.model_dump()
        data['published_date'] = old_metadata.published_date.isoformat()
        json.dump(data, f)

    # モックの設定（新しいデータ）
    mock_arxiv_client.get_metadata = AsyncMock(return_value=sample_paper_metadata)

    # 実行
    result = await paper_service.get_metadata("2301.00001", force_refresh=True)

    # 検証
    assert result.title == "Test Paper"  # 新しいタイトル
    mock_arxiv_client.get_metadata.assert_called_once()


@pytest.mark.asyncio
async def test_get_metadata_arxiv_error(paper_service, mock_arxiv_client):
    """メタデータ取得でArxivClientErrorが発生"""
    # モックの設定
    mock_arxiv_client.get_metadata = AsyncMock(
        side_effect=ArxivClientError("API error")
    )

    # 実行と検証
    with pytest.raises(PaperServiceError, match="Failed to get metadata"):
        await paper_service.get_metadata("2301.00001")


@pytest.mark.asyncio
async def test_get_metadata_unexpected_error(paper_service, mock_arxiv_client):
    """メタデータ取得で予期しないエラーが発生"""
    # モックの設定
    mock_arxiv_client.get_metadata = AsyncMock(
        side_effect=RuntimeError("Unexpected error")
    )

    # 実行と検証
    with pytest.raises(PaperServiceError, match="Unexpected error"):
        await paper_service.get_metadata("2301.00001")


# ========================================
# extract_text tests
# ========================================

@pytest.mark.asyncio
async def test_extract_text_from_pdf(paper_service, tmp_path):
    """PDFからテキストを抽出"""
    # テスト用PDFファイルを作成
    pdf_path = tmp_path / "test.pdf"

    # pypdf.PdfReaderをモック
    with patch('src.services.paper_service.PdfReader') as mock_pdf_reader:
        mock_page = Mock()
        mock_page.extract_text.return_value = "This is test text."
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        # PDFファイルを作成（空でOK）
        pdf_path.write_text("")

        # 実行
        text = await paper_service.extract_text(pdf_path)

        # 検証
        assert "This is test text." in text


@pytest.mark.asyncio
async def test_extract_text_multiple_pages(paper_service, tmp_path):
    """複数ページのPDFからテキストを抽出"""
    pdf_path = tmp_path / "test.pdf"

    with patch('src.services.paper_service.PdfReader') as mock_pdf_reader:
        # 3ページ分のモック
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 text."
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2 text."
        mock_page3 = Mock()
        mock_page3.extract_text.return_value = "Page 3 text."

        mock_reader = Mock()
        mock_reader.pages = [mock_page1, mock_page2, mock_page3]
        mock_pdf_reader.return_value = mock_reader

        pdf_path.write_text("")

        # 実行
        text = await paper_service.extract_text(pdf_path)

        # 検証
        assert "Page 1 text." in text
        assert "Page 2 text." in text
        assert "Page 3 text." in text


@pytest.mark.asyncio
async def test_extract_text_page_extraction_error(paper_service, tmp_path):
    """一部のページでエラーが発生しても続行"""
    pdf_path = tmp_path / "test.pdf"

    with patch('src.services.paper_service.PdfReader') as mock_pdf_reader:
        # 2ページ目でエラー
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 text."
        mock_page2 = Mock()
        mock_page2.extract_text.side_effect = Exception("Extraction error")
        mock_page3 = Mock()
        mock_page3.extract_text.return_value = "Page 3 text."

        mock_reader = Mock()
        mock_reader.pages = [mock_page1, mock_page2, mock_page3]
        mock_pdf_reader.return_value = mock_reader

        pdf_path.write_text("")

        # 実行
        text = await paper_service.extract_text(pdf_path)

        # 検証（エラーページはスキップされる）
        assert "Page 1 text." in text
        assert "Page 3 text." in text
        assert "Page 2 text." not in text


@pytest.mark.asyncio
async def test_extract_text_file_not_found(paper_service, tmp_path):
    """存在しないPDFファイルでエラー"""
    pdf_path = tmp_path / "nonexistent.pdf"

    # 実行と検証
    with pytest.raises(PaperServiceError, match="PDF file not found"):
        await paper_service.extract_text(pdf_path)


@pytest.mark.asyncio
async def test_extract_text_pdf_reader_error(paper_service, tmp_path):
    """PdfReaderでエラーが発生"""
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_text("")

    with patch('src.services.paper_service.PdfReader') as mock_pdf_reader:
        mock_pdf_reader.side_effect = Exception("PDF read error")

        # 実行と検証
        with pytest.raises(PaperServiceError, match="Failed to extract text"):
            await paper_service.extract_text(pdf_path)


# ========================================
# Initialization tests
# ========================================

def test_paper_service_initialization(mock_arxiv_client, tmp_path):
    """PaperServiceの初期化でディレクトリが作成される"""
    cache_dir = tmp_path / "cache"

    # 実行
    service = PaperService(
        arxiv_client=mock_arxiv_client,
        cache_dir=cache_dir
    )

    # 検証
    assert service.cache_dir == cache_dir
    assert service.pdf_cache_dir.exists()
    assert service.metadata_cache_dir.exists()
    assert service.pdf_cache_dir == cache_dir / "pdfs"
    assert service.metadata_cache_dir == cache_dir / "metadata"
