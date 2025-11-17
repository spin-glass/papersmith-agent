# -*- coding: utf-8 -*-
"""FastAPI エンドポイントのユニットテスト

Requirements: 9.1, 9.2, 9.3, 9.5

このテストファイルは以下をカバーします:
- GET /health エンドポイント
- POST /papers/search エンドポイント
- POST /papers/download エンドポイント
- POST /rag/query エンドポイント
- エラーレスポンス（503、500、400）
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from datetime import datetime

from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.api.main import app
from src.models.paper import PaperMetadata
from src.models.rag import SearchResult, RAGResponse
from src.utils.errors import IndexNotReadyError, APIError, LLMError


# ===== Fixtures =====

@pytest.fixture
def client():
    """TestClientフィクスチャ
    
    FastAPIのTestClientを提供します。
    """
    return TestClient(app)


@pytest.fixture
async def async_client():
    """AsyncClientフィクスチャ
    
    非同期テスト用のAsyncClientを提供します。
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_index_holder_ready():
    """準備完了状態のindex_holderモック"""
    with patch("src.api.main.index_holder") as mock_holder:
        mock_chroma = MagicMock()
        mock_chroma.count.return_value = 100
        
        mock_holder.is_ready.return_value = True
        mock_holder.size.return_value = 100
        mock_holder.get = AsyncMock(return_value=mock_chroma)
        
        yield mock_holder


@pytest.fixture
def mock_index_holder_not_ready():
    """未準備状態のindex_holderモック"""
    with patch("src.api.main.index_holder") as mock_holder:
        mock_holder.is_ready.return_value = False
        mock_holder.size.return_value = 0
        mock_holder.get = AsyncMock(side_effect=RuntimeError("Index not ready"))
        
        yield mock_holder


@pytest.fixture
def sample_papers():
    """サンプル論文リスト"""
    return [
        PaperMetadata(
            arxiv_id="2301.00001",
            title="Example Paper 1",
            authors=["Alice Smith"],
            abstract="Abstract 1",
            year=2023,
            categories=["cs.AI"],
            pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
            published_date=datetime(2023, 1, 1)
        ),
        PaperMetadata(
            arxiv_id="2301.00002",
            title="Example Paper 2",
            authors=["Bob Johnson"],
            abstract="Abstract 2",
            year=2023,
            categories=["cs.LG"],
            pdf_url="https://arxiv.org/pdf/2301.00002.pdf",
            published_date=datetime(2023, 1, 2)
        )
    ]


@pytest.fixture
def sample_rag_response():
    """サンプルRAGレスポンス"""
    return RAGResponse(
        answer="これはテスト回答です。",
        sources=[
            SearchResult(
                chunk_id="2301.00001_intro_0",
                text="Sample text",
                score=0.85,
                metadata={"arxiv_id": "2301.00001"}
            )
        ],
        metadata={"model": "test-model"}
    )


# ===== GET /health Tests =====

def test_health_check_ready(client, mock_index_holder_ready):
    """GET /health - インデックス準備完了時のテスト
    
    Requirements: 9.2
    """
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert data["index_ready"] is True
    assert data["index_size"] == 100


def test_health_check_not_ready(client, mock_index_holder_not_ready):
    """GET /health - インデックス未準備時のテスト
    
    Requirements: 9.2
    """
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "initializing"
    assert data["index_ready"] is False
    assert data["index_size"] == 0


# ===== POST /papers/search Tests =====

def test_search_papers_success(client, sample_papers):
    """POST /papers/search - 正常な検索のテスト
    
    Requirements: 9.3
    """
    with patch("src.api.main.paper_service") as mock_service:
        mock_service.search_papers = AsyncMock(return_value=sample_papers)
        
        response = client.post(
            "/papers/search",
            json={"query": "machine learning", "max_results": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["count"] == 2
        assert len(data["papers"]) == 2
        assert data["papers"][0]["arxiv_id"] == "2301.00001"
        assert data["papers"][1]["arxiv_id"] == "2301.00002"
        
        # サービスが正しく呼ばれたか確認
        mock_service.search_papers.assert_called_once_with(
            query="machine learning",
            max_results=10
        )


def test_search_papers_with_custom_max_results(client, sample_papers):
    """POST /papers/search - max_resultsカスタマイズのテスト
    
    Requirements: 9.3
    """
    with patch("src.api.main.paper_service") as mock_service:
        mock_service.search_papers = AsyncMock(return_value=sample_papers[:1])
        
        response = client.post(
            "/papers/search",
            json={"query": "deep learning", "max_results": 1}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["count"] == 1
        assert len(data["papers"]) == 1


def test_search_papers_service_not_initialized(client):
    """POST /papers/search - サービス未初期化時のテスト
    
    Requirements: 9.5
    """
    with patch("src.api.main.paper_service", None):
        response = client.post(
            "/papers/search",
            json={"query": "test", "max_results": 10}
        )
        
        assert response.status_code == 503
        assert "not initialized" in response.json()["detail"]


def test_search_papers_service_error(client):
    """POST /papers/search - サービスエラー時のテスト
    
    Requirements: 9.5
    """
    with patch("src.api.main.paper_service") as mock_service:
        mock_service.search_papers = AsyncMock(
            side_effect=Exception("API connection failed")
        )
        
        response = client.post(
            "/papers/search",
            json={"query": "test", "max_results": 10}
        )
        
        assert response.status_code == 500
        assert "論文検索に失敗しました" in response.json()["detail"]


def test_search_papers_invalid_max_results(client):
    """POST /papers/search - 無効なmax_resultsのテスト
    
    Requirements: 9.5
    """
    # max_results が範囲外（0以下）
    response = client.post(
        "/papers/search",
        json={"query": "test", "max_results": 0}
    )
    assert response.status_code == 422  # Validation error
    
    # max_results が範囲外（100超）
    response = client.post(
        "/papers/search",
        json={"query": "test", "max_results": 101}
    )
    assert response.status_code == 422  # Validation error


# ===== POST /papers/download Tests =====

def test_download_paper_success(client, mock_index_holder_ready, sample_papers):
    """POST /papers/download - 正常なダウンロードのテスト
    
    Requirements: 9.3
    """
    with patch("src.api.main.paper_service") as mock_paper_service, \
         patch("src.api.main.embedding_service") as mock_embed_service, \
         patch("src.services.rag_service.RAGService") as mock_rag_service_class:
        
        # PaperServiceのモック
        mock_paper_service.get_metadata = AsyncMock(return_value=sample_papers[0])
        mock_paper_service.download_pdf = AsyncMock(
            return_value=Path("./cache/pdfs/2301.00001.pdf")
        )
        mock_paper_service.extract_text = AsyncMock(
            return_value="Sample paper text"
        )
        
        # RAGServiceのモック
        mock_rag_instance = MagicMock()
        mock_rag_instance.index_paper = AsyncMock(return_value=10)
        mock_rag_service_class.return_value = mock_rag_instance
        
        response = client.post(
            "/papers/download",
            json={"arxiv_id": "2301.00001"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["arxiv_id"] == "2301.00001"
        assert data["indexed_chunks"] == 10
        assert "正常にダウンロード" in data["message"]
        
        # サービスが正しく呼ばれたか確認
        mock_paper_service.get_metadata.assert_called_once_with("2301.00001")
        mock_paper_service.download_pdf.assert_called_once()
        mock_paper_service.extract_text.assert_called_once()
        mock_rag_instance.index_paper.assert_called_once()


def test_download_paper_services_not_initialized(client):
    """POST /papers/download - サービス未初期化時のテスト
    
    Requirements: 9.5
    """
    with patch("src.api.main.paper_service", None):
        response = client.post(
            "/papers/download",
            json={"arxiv_id": "2301.00001"}
        )
        
        assert response.status_code == 503
        assert "not initialized" in response.json()["detail"]


def test_download_paper_index_not_ready(client, mock_index_holder_not_ready):
    """POST /papers/download - インデックス未準備時のテスト
    
    Requirements: 9.2, 9.5
    """
    with patch("src.api.main.paper_service") as mock_service, \
         patch("src.api.main.embedding_service"):
        
        mock_service.get_metadata = AsyncMock(return_value=MagicMock())
        
        response = client.post(
            "/papers/download",
            json={"arxiv_id": "2301.00001"}
        )
        
        # index_holder.get()がRuntimeErrorを投げるので503エラー
        assert response.status_code == 503


def test_download_paper_download_error(client, mock_index_holder_ready, sample_papers):
    """POST /papers/download - ダウンロードエラー時のテスト
    
    Requirements: 9.5
    """
    with patch("src.api.main.paper_service") as mock_service, \
         patch("src.api.main.embedding_service"):
        
        mock_service.get_metadata = AsyncMock(return_value=sample_papers[0])
        mock_service.download_pdf = AsyncMock(
            side_effect=Exception("Download failed")
        )
        
        response = client.post(
            "/papers/download",
            json={"arxiv_id": "2301.00001"}
        )
        
        assert response.status_code == 500
        assert "ダウンロードとインデックス化に失敗" in response.json()["detail"]


# ===== POST /rag/query Tests =====

def test_rag_query_success(client, mock_index_holder_ready, sample_rag_response):
    """POST /rag/query - 正常なRAGクエリのテスト
    
    Requirements: 9.3
    """
    with patch("src.api.main.embedding_service") as mock_embed, \
         patch("src.api.main.llm_service") as mock_llm, \
         patch("src.api.main.basic_rag_query", new_callable=AsyncMock) as mock_rag_query:
        
        mock_rag_query.return_value = sample_rag_response
        
        response = client.post(
            "/rag/query",
            json={
                "question": "What is machine learning?",
                "arxiv_ids": ["2301.00001"],
                "top_k": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["answer"] == "これはテスト回答です。"
        assert len(data["sources"]) == 1
        assert data["sources"][0]["chunk_id"] == "2301.00001_intro_0"
        
        # basic_rag_queryが正しく呼ばれたか確認
        mock_rag_query.assert_called_once()
        call_kwargs = mock_rag_query.call_args[1]
        assert call_kwargs["question"] == "What is machine learning?"
        assert call_kwargs["arxiv_ids"] == ["2301.00001"]
        assert call_kwargs["top_k"] == 5


def test_rag_query_without_arxiv_ids(client, mock_index_holder_ready, sample_rag_response):
    """POST /rag/query - arxiv_idsなしのテスト
    
    Requirements: 9.3
    """
    with patch("src.api.main.embedding_service"), \
         patch("src.api.main.llm_service"), \
         patch("src.api.main.basic_rag_query", new_callable=AsyncMock) as mock_rag_query:
        
        mock_rag_query.return_value = sample_rag_response
        
        response = client.post(
            "/rag/query",
            json={"question": "What is deep learning?"}
        )
        
        assert response.status_code == 200
        
        # arxiv_idsがNoneで呼ばれることを確認
        call_kwargs = mock_rag_query.call_args[1]
        assert call_kwargs["arxiv_ids"] is None


def test_rag_query_services_not_initialized(client):
    """POST /rag/query - サービス未初期化時のテスト
    
    Requirements: 9.5
    """
    with patch("src.api.main.embedding_service", None):
        response = client.post(
            "/rag/query",
            json={"question": "test"}
        )
        
        assert response.status_code == 503
        assert "not initialized" in response.json()["detail"]


def test_rag_query_index_not_ready(client, mock_index_holder_not_ready):
    """POST /rag/query - インデックス未準備時のテスト
    
    Requirements: 9.2, 9.5
    """
    with patch("src.api.main.embedding_service"), \
         patch("src.api.main.llm_service"):
        
        response = client.post(
            "/rag/query",
            json={"question": "test"}
        )
        
        assert response.status_code == 503


def test_rag_query_execution_error(client, mock_index_holder_ready):
    """POST /rag/query - クエリ実行エラー時のテスト
    
    Requirements: 9.5
    """
    with patch("src.api.main.embedding_service"), \
         patch("src.api.main.llm_service"), \
         patch("src.api.main.basic_rag_query", new_callable=AsyncMock) as mock_rag_query:
        
        mock_rag_query.side_effect = Exception("Query execution failed")
        
        response = client.post(
            "/rag/query",
            json={"question": "test"}
        )
        
        assert response.status_code == 500
        assert "RAGクエリの実行に失敗" in response.json()["detail"]


def test_rag_query_invalid_top_k(client):
    """POST /rag/query - 無効なtop_kのテスト
    
    Requirements: 9.5
    """
    # top_k が範囲外（0以下）
    response = client.post(
        "/rag/query",
        json={"question": "test", "top_k": 0}
    )
    assert response.status_code == 422  # Validation error
    
    # top_k が範囲外（20超）
    response = client.post(
        "/rag/query",
        json={"question": "test", "top_k": 21}
    )
    assert response.status_code == 422  # Validation error


# ===== Error Handler Tests =====

def test_index_not_ready_error_handler(client):
    """IndexNotReadyErrorハンドラーのテスト
    
    Requirements: 9.2, 9.5
    """
    with patch("src.api.main.index_holder") as mock_holder:
        mock_holder.is_ready.return_value = False
        mock_holder.get = AsyncMock(
            side_effect=RuntimeError("Index not ready. Please wait for initialization to complete.")
        )
        
        with patch("src.api.main.embedding_service"), \
             patch("src.api.main.llm_service"):
            
            response = client.post(
                "/rag/query",
                json={"question": "test"}
            )
            
            assert response.status_code == 503
            data = response.json()
            assert "インデックス構築中" in data["detail"]
            assert data["status"] == "initializing"


def test_api_error_handler(client):
    """APIErrorハンドラーのテスト
    
    Requirements: 9.5
    """
    with patch("src.api.main.paper_service") as mock_service:
        mock_service.search_papers = AsyncMock(
            side_effect=APIError(
                message="arXiv API error",
                api_name="arXiv",
                status_code=500
            )
        )
        
        response = client.post(
            "/papers/search",
            json={"query": "test", "max_results": 10}
        )
        
        # APIErrorは内部で500エラーになる
        assert response.status_code == 500


def test_llm_error_handler(client, mock_index_holder_ready):
    """LLMErrorハンドラーのテスト
    
    Requirements: 9.5
    """
    with patch("src.api.main.embedding_service"), \
         patch("src.api.main.llm_service"), \
         patch("src.api.main.basic_rag_query", new_callable=AsyncMock) as mock_rag_query:
        
        mock_rag_query.side_effect = LLMError(
            message="LLM inference failed",
            model_name="test-model"
        )
        
        response = client.post(
            "/rag/query",
            json={"question": "test"}
        )
        
        # LLMErrorは内部で500エラーになる
        assert response.status_code == 500


# ===== Root Endpoint Test =====

def test_root_endpoint(client):
    """GET / - ルートエンドポイントのテスト
    
    Requirements: 9.1
    """
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == "Papersmith Agent API"
    assert data["version"] == "1.0.0"
    assert data["status"] == "running"
    assert data["docs"] == "/docs"


# ===== Additional Error Handler Tests =====

def test_papersmith_error_handler(client):
    """PapersmithErrorハンドラーのテスト
    
    Requirements: 9.5
    """
    from src.utils.errors import PapersmithError
    
    with patch("src.api.main.paper_service") as mock_service:
        mock_service.search_papers = AsyncMock(
            side_effect=PapersmithError(
                message="Generic Papersmith error",
                details={"error_code": "TEST_ERROR"}
            )
        )
        
        response = client.post(
            "/papers/search",
            json={"query": "test", "max_results": 10}
        )
        
        # PapersmithErrorは内部で500エラーになる
        assert response.status_code == 500


def test_general_exception_handler(client):
    """一般的な例外ハンドラーのテスト
    
    Requirements: 9.5
    """
    with patch("src.api.main.paper_service") as mock_service:
        # 予期しない例外をスロー
        mock_service.search_papers = AsyncMock(
            side_effect=ValueError("Unexpected error")
        )
        
        response = client.post(
            "/papers/search",
            json={"query": "test", "max_results": 10}
        )
        
        assert response.status_code == 500
        # エンドポイント内でキャッチされてカスタムメッセージになる
        assert "論文検索に失敗しました" in response.json()["detail"]


# ===== POST /admin/init-index Tests =====

def test_init_index_success(client, mock_index_holder_ready, sample_papers):
    """POST /admin/init-index - 正常なインデックス初期化のテスト
    
    Requirements: 9.3
    """
    with patch("src.api.main.paper_service") as mock_paper_service, \
         patch("src.api.main.embedding_service"), \
         patch("src.services.rag_service.RAGService") as mock_rag_service_class, \
         patch("pathlib.Path.exists") as mock_exists, \
         patch("pathlib.Path.glob") as mock_glob:
        
        # PDFキャッシュディレクトリが存在する
        mock_exists.return_value = True
        
        # 2つのPDFファイルが存在する
        mock_pdf1 = MagicMock()
        mock_pdf1.stem = "2301_00001"
        mock_pdf2 = MagicMock()
        mock_pdf2.stem = "2301_00002"
        mock_glob.return_value = [mock_pdf1, mock_pdf2]
        
        # PaperServiceのモック
        mock_paper_service.get_metadata = AsyncMock(return_value=sample_papers[0])
        mock_paper_service.extract_text = AsyncMock(return_value="Sample text")
        
        # RAGServiceのモック
        mock_rag_instance = MagicMock()
        mock_rag_instance.index_paper = AsyncMock(return_value=5)
        mock_rag_service_class.return_value = mock_rag_instance
        
        response = client.post(
            "/admin/init-index",
            json={"force": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["indexed_count"] == 10  # 2 PDFs × 5 chunks each


def test_init_index_no_cache_directory(client, mock_index_holder_ready):
    """POST /admin/init-index - キャッシュディレクトリなしのテスト
    
    Requirements: 9.3
    """
    with patch("src.api.main.paper_service"), \
         patch("src.api.main.embedding_service"), \
         patch("pathlib.Path.exists") as mock_exists:
        
        # PDFキャッシュディレクトリが存在しない
        mock_exists.return_value = False
        
        response = client.post(
            "/admin/init-index",
            json={"force": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["indexed_count"] == 0
        assert "存在しません" in data["message"]


def test_init_index_force_reset(client, mock_index_holder_ready):
    """POST /admin/init-index - 強制リセットのテスト
    
    Requirements: 9.3
    """
    with patch("src.api.main.paper_service"), \
         patch("src.api.main.embedding_service"), \
         patch("pathlib.Path.exists") as mock_exists:
        
        mock_exists.return_value = False
        
        # Chromaクライアントのresetメソッドが呼ばれることを確認
        mock_chroma = mock_index_holder_ready.get.return_value
        mock_chroma.reset = MagicMock()
        
        response = client.post(
            "/admin/init-index",
            json={"force": True}
        )
        
        assert response.status_code == 200
        mock_chroma.reset.assert_called_once()


def test_init_index_services_not_initialized(client):
    """POST /admin/init-index - サービス未初期化時のテスト
    
    Requirements: 9.5
    """
    with patch("src.api.main.paper_service", None):
        response = client.post(
            "/admin/init-index",
            json={"force": False}
        )
        
        assert response.status_code == 503
        assert "not initialized" in response.json()["detail"]


def test_init_index_error(client, mock_index_holder_ready):
    """POST /admin/init-index - 初期化エラー時のテスト
    
    Requirements: 9.5
    """
    with patch("src.api.main.paper_service"), \
         patch("src.api.main.embedding_service"), \
         patch("pathlib.Path.exists") as mock_exists:
        
        mock_exists.side_effect = Exception("Filesystem error")
        
        response = client.post(
            "/admin/init-index",
            json={"force": False}
        )
        
        assert response.status_code == 500
        assert "インデックスの初期化に失敗" in response.json()["detail"]


def test_init_index_partial_failure(client, mock_index_holder_ready, sample_papers):
    """POST /admin/init-index - 一部のPDFが失敗する場合のテスト
    
    Requirements: 9.3, 9.5
    """
    with patch("src.api.main.paper_service") as mock_paper_service, \
         patch("src.api.main.embedding_service"), \
         patch("src.services.rag_service.RAGService") as mock_rag_service_class, \
         patch("pathlib.Path.exists") as mock_exists, \
         patch("pathlib.Path.glob") as mock_glob:
        
        # PDFキャッシュディレクトリが存在する
        mock_exists.return_value = True
        
        # 2つのPDFファイルが存在する
        mock_pdf1 = MagicMock()
        mock_pdf1.stem = "2301_00001"
        mock_pdf2 = MagicMock()
        mock_pdf2.stem = "2301_00002"
        mock_glob.return_value = [mock_pdf1, mock_pdf2]
        
        # 最初のPDFは成功、2番目は失敗
        call_count = [0]
        
        async def mock_get_metadata_side_effect(arxiv_id):
            call_count[0] += 1
            if call_count[0] == 1:
                return sample_papers[0]
            else:
                raise Exception("Metadata fetch failed")
        
        mock_paper_service.get_metadata = mock_get_metadata_side_effect
        mock_paper_service.extract_text = AsyncMock(return_value="Sample text")
        
        # RAGServiceのモック
        mock_rag_instance = MagicMock()
        mock_rag_instance.index_paper = AsyncMock(return_value=5)
        mock_rag_service_class.return_value = mock_rag_instance
        
        response = client.post(
            "/admin/init-index",
            json={"force": False}
        )
        
        # 一部失敗しても成功を返す（エラーはログに記録される）
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        # 1つのPDFのみ成功
        assert data["indexed_count"] == 5
