# -*- coding: utf-8 -*-
"""ArxivClientのユニットテスト

Requirements: 1.1, 1.4
"""

import pytest
import arxiv
import httpx
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime

from src.clients.arxiv_client import ArxivClient, ArxivClientError
from src.models.paper import PaperMetadata


@pytest.fixture
def arxiv_client(tmp_path):
    """ArxivClientインスタンス"""
    return ArxivClient(
        cache_dir=tmp_path / "pdfs",
        max_retries=3,
        timeout=30
    )


@pytest.fixture
def mock_arxiv_result():
    """モックarxiv.Result"""
    result = Mock(spec=arxiv.Result)
    result.entry_id = "http://arxiv.org/abs/2301.00001v1"
    result.title = "Test Paper Title"
    
    # 著者モック（.name属性を持つ）
    author1 = Mock()
    author1.name = "Author One"
    author2 = Mock()
    author2.name = "Author Two"
    result.authors = [author1, author2]
    
    result.summary = "This is a test abstract."
    result.published = datetime(2023, 1, 1)
    result.categories = ["cs.AI", "cs.LG"]
    result.pdf_url = "https://arxiv.org/pdf/2301.00001.pdf"
    result.doi = "10.1234/test.doi"
    return result


# ========================================
# Initialization tests
# ========================================

def test_arxiv_client_initialization(tmp_path):
    """ArxivClientの初期化"""
    cache_dir = tmp_path / "pdfs"
    client = ArxivClient(
        cache_dir=cache_dir,
        max_retries=5,
        timeout=60
    )
    
    assert client.cache_dir == cache_dir
    assert client.cache_dir.exists()
    assert client.max_retries == 5
    assert client.timeout == 60
    assert client.client is not None


# ========================================
# search_papers tests
# ========================================

@pytest.mark.asyncio
async def test_search_papers_success(arxiv_client, mock_arxiv_result):
    """論文検索が成功する"""
    # モックの設定
    with patch.object(arxiv_client.client, 'results', return_value=[mock_arxiv_result]):
        # 実行
        results = await arxiv_client.search_papers("machine learning", max_results=10)
        
        # 検証
        assert len(results) == 1
        assert isinstance(results[0], PaperMetadata)
        assert results[0].arxiv_id == "2301.00001"
        assert results[0].title == "Test Paper Title"
        assert results[0].authors == ["Author One", "Author Two"]


@pytest.mark.asyncio
async def test_search_papers_empty_results(arxiv_client):
    """論文検索で結果が0件"""
    # モックの設定
    with patch.object(arxiv_client.client, 'results', return_value=[]):
        # 実行
        results = await arxiv_client.search_papers("nonexistent query")
        
        # 検証
        assert len(results) == 0


@pytest.mark.asyncio
async def test_search_papers_multiple_results(arxiv_client, mock_arxiv_result):
    """複数の論文を検索"""
    # 3つの結果を作成
    result1 = mock_arxiv_result
    result2 = Mock(spec=arxiv.Result)
    result2.entry_id = "http://arxiv.org/abs/2301.00002v1"
    result2.title = "Paper 2"
    author3 = Mock()
    author3.name = "Author Three"
    result2.authors = [author3]
    result2.summary = "Abstract 2"
    result2.published = datetime(2023, 1, 2)
    result2.categories = ["cs.AI"]
    result2.pdf_url = "https://arxiv.org/pdf/2301.00002.pdf"
    result2.doi = None
    
    result3 = Mock(spec=arxiv.Result)
    result3.entry_id = "http://arxiv.org/abs/2301.00003v1"
    result3.title = "Paper 3"
    author4 = Mock()
    author4.name = "Author Four"
    result3.authors = [author4]
    result3.summary = "Abstract 3"
    result3.published = datetime(2023, 1, 3)
    result3.categories = ["cs.LG"]
    result3.pdf_url = "https://arxiv.org/pdf/2301.00003.pdf"
    result3.doi = None
    
    # モックの設定
    with patch.object(arxiv_client.client, 'results', return_value=[result1, result2, result3]):
        # 実行
        results = await arxiv_client.search_papers("test", max_results=3)
        
        # 検証
        assert len(results) == 3
        assert results[0].arxiv_id == "2301.00001"
        assert results[1].arxiv_id == "2301.00002"
        assert results[2].arxiv_id == "2301.00003"


@pytest.mark.asyncio
async def test_search_papers_unexpected_error(arxiv_client):
    """論文検索で予期しないエラーが発生"""
    # モックの設定
    with patch.object(arxiv_client.client, 'results', side_effect=RuntimeError("Unexpected")):
        # 実行と検証
        with pytest.raises(ArxivClientError, match="Unexpected error"):
            await arxiv_client.search_papers("test query")


# ========================================
# get_metadata tests
# ========================================

@pytest.mark.asyncio
async def test_get_metadata_success(arxiv_client, mock_arxiv_result):
    """メタデータ取得が成功する"""
    # モックの設定
    with patch.object(arxiv_client.client, 'results', return_value=[mock_arxiv_result]):
        # 実行
        metadata = await arxiv_client.get_metadata("2301.00001")
        
        # 検証
        assert isinstance(metadata, PaperMetadata)
        assert metadata.arxiv_id == "2301.00001"
        assert metadata.title == "Test Paper Title"


@pytest.mark.asyncio
async def test_get_metadata_not_found(arxiv_client):
    """論文が見つからない"""
    # モックの設定
    with patch.object(arxiv_client.client, 'results', return_value=[]):
        # 実行と検証
        with pytest.raises(ArxivClientError, match="Paper not found"):
            await arxiv_client.get_metadata("9999.99999")


@pytest.mark.asyncio
async def test_get_metadata_unexpected_error(arxiv_client):
    """メタデータ取得で予期しないエラーが発生"""
    # モックの設定
    with patch.object(arxiv_client.client, 'results', side_effect=RuntimeError("Unexpected")):
        # 実行と検証
        with pytest.raises(ArxivClientError, match="Unexpected error"):
            await arxiv_client.get_metadata("2301.00001")


# ========================================
# download_pdf tests
# ========================================

@pytest.mark.asyncio
async def test_download_pdf_success(arxiv_client, tmp_path):
    """PDFダウンロードが成功する"""
    # モックHTTPレスポンス
    mock_response = Mock()
    mock_response.content = b"PDF content"
    mock_response.raise_for_status = Mock()
    
    # httpx.AsyncClientをモック
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        # 実行
        pdf_path = await arxiv_client.download_pdf("2301.00001")
        
        # 検証
        assert pdf_path.exists()
        assert pdf_path.name == "2301.00001.pdf"
        assert pdf_path.read_bytes() == b"PDF content"


@pytest.mark.asyncio
async def test_download_pdf_with_custom_url(arxiv_client):
    """カスタムPDF URLでダウンロード"""
    # モックHTTPレスポンス
    mock_response = Mock()
    mock_response.content = b"PDF content"
    mock_response.raise_for_status = Mock()
    
    # httpx.AsyncClientをモック
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        # 実行
        custom_url = "https://custom.url/paper.pdf"
        pdf_path = await arxiv_client.download_pdf("2301.00001", pdf_url=custom_url)
        
        # 検証
        assert pdf_path.exists()
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == custom_url


@pytest.mark.asyncio
async def test_download_pdf_cached(arxiv_client, tmp_path):
    """キャッシュ済みPDFは再ダウンロードしない"""
    # キャッシュファイルを作成
    cache_dir = tmp_path / "pdfs"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached_pdf = cache_dir / "2301.00001.pdf"
    cached_pdf.write_bytes(b"Cached PDF content")
    
    # 実行（HTTPクライアントはモックしない）
    pdf_path = await arxiv_client.download_pdf("2301.00001")
    
    # 検証
    assert pdf_path == cached_pdf
    assert pdf_path.read_bytes() == b"Cached PDF content"


@pytest.mark.asyncio
async def test_download_pdf_http_error(arxiv_client):
    """PDFダウンロードでHTTPエラーが発生"""
    # httpx.AsyncClientをモック
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(side_effect=httpx.HTTPError("HTTP error"))
        mock_client_class.return_value = mock_client
        
        # 実行と検証
        with pytest.raises(ArxivClientError, match="Failed to download PDF"):
            await arxiv_client.download_pdf("2301.00001")


@pytest.mark.asyncio
async def test_download_pdf_unexpected_error(arxiv_client):
    """PDFダウンロードで予期しないエラーが発生"""
    # httpx.AsyncClientをモック
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(side_effect=RuntimeError("Unexpected"))
        mock_client_class.return_value = mock_client
        
        # 実行と検証
        with pytest.raises(ArxivClientError, match="Unexpected error"):
            await arxiv_client.download_pdf("2301.00001")


# ========================================
# _convert_to_metadata tests
# ========================================

def test_convert_to_metadata(arxiv_client, mock_arxiv_result):
    """arxiv.ResultをPaperMetadataに変換"""
    # 実行
    metadata = arxiv_client._convert_to_metadata(mock_arxiv_result)
    
    # 検証
    assert isinstance(metadata, PaperMetadata)
    assert metadata.arxiv_id == "2301.00001"
    assert metadata.title == "Test Paper Title"
    assert metadata.authors == ["Author One", "Author Two"]
    assert metadata.abstract == "This is a test abstract."
    assert metadata.year == 2023
    assert metadata.categories == ["cs.AI", "cs.LG"]
    assert metadata.pdf_url == "https://arxiv.org/pdf/2301.00001.pdf"
    assert metadata.doi == "10.1234/test.doi"
    assert metadata.published_date == datetime(2023, 1, 1)


def test_convert_to_metadata_without_doi(arxiv_client, mock_arxiv_result):
    """DOIがない場合"""
    # DOIを削除
    delattr(mock_arxiv_result, 'doi')
    
    # 実行
    metadata = arxiv_client._convert_to_metadata(mock_arxiv_result)
    
    # 検証
    assert metadata.doi is None


def test_convert_to_metadata_normalizes_arxiv_id(arxiv_client, mock_arxiv_result):
    """arXiv IDを正規化（バージョン番号を除去）"""
    # バージョン番号付きのID
    mock_arxiv_result.entry_id = "http://arxiv.org/abs/2301.00001v3"
    
    # 実行
    metadata = arxiv_client._convert_to_metadata(mock_arxiv_result)
    
    # 検証
    assert metadata.arxiv_id == "2301.00001"


def test_convert_to_metadata_extracts_year(arxiv_client, mock_arxiv_result):
    """発行年を抽出"""
    mock_arxiv_result.published = datetime(2024, 6, 15)
    
    # 実行
    metadata = arxiv_client._convert_to_metadata(mock_arxiv_result)
    
    # 検証
    assert metadata.year == 2024
