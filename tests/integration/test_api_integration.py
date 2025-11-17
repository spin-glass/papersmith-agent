# -*- coding: utf-8 -*-
"""API統合テスト

Requirements: 9.1, 9.2, 9.3

このテストはFastAPIのTestClientを使用し、実際のChromaDBを使用します。
LLMはモックを使用してテストを高速化します。
"""

import pytest
import pytest_asyncio
from pathlib import Path
import tempfile
import shutil
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from src.api.main import app
from src.clients.chroma_client import ChromaClient
from src.models.config import ChromaConfig, EmbeddingConfig, LLMConfig


@pytest.fixture
def temp_dirs():
    """一時的なディレクトリを作成"""
    temp_base = Path(tempfile.mkdtemp())
    dirs = {
        "cache": temp_base / "cache",
        "chroma": temp_base / "chroma",
        "logs": temp_base / "logs"
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    
    yield dirs
    
    # クリーンアップ
    if temp_base.exists():
        shutil.rmtree(temp_base)


@pytest.fixture
def mock_services(mock_embedding_service, mock_llm_service):
    """モックサービスを提供"""
    return {
        "embedding": mock_embedding_service,
        "llm": mock_llm_service
    }


@pytest.fixture
def client(temp_dirs, mock_services):
    """TestClientを作成
    
    実際のChromaDBを使用し、LLM/Embeddingはモックを使用します。
    """
    # 環境変数を設定
    with patch.dict("os.environ", {
        "CHROMA_PERSIST_DIR": str(temp_dirs["chroma"]),
        "CHROMA_COLLECTION_NAME": "test_api_collection",
        "CACHE_DIR": str(temp_dirs["cache"]),
        "LOG_DIR": str(temp_dirs["logs"]),
        "LLM_BACKEND": "gemini",
        "EMBEDDING_BACKEND": "gemini"
    }):
        # サービスをモックに置き換え
        with patch("src.api.main.EmbeddingService") as mock_emb_cls, \
             patch("src.api.main.LLMService") as mock_llm_cls:
            
            # モックサービスを返すように設定
            mock_emb_instance = MagicMock()
            mock_emb_instance.load_model = AsyncMock()
            mock_emb_instance.embed = mock_services["embedding"].embed
            mock_emb_instance.embed_batch = mock_services["embedding"].embed_batch
            mock_emb_cls.return_value = mock_emb_instance
            
            mock_llm_instance = MagicMock()
            mock_llm_instance.load_model = AsyncMock()
            mock_llm_instance.generate = mock_services["llm"].generate
            mock_llm_cls.return_value = mock_llm_instance
            
            # TestClientを作成
            with TestClient(app) as test_client:
                yield test_client


def test_health_endpoint(client):
    """ヘルスチェックエンドポイントのテスト
    
    Requirements: 9.1, 9.2
    """
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "index_ready" in data
    assert "index_size" in data
    assert data["status"] in ["ok", "initializing"]
    assert isinstance(data["index_ready"], bool)
    assert isinstance(data["index_size"], int)


def test_search_papers_endpoint(client):
    """論文検索エンドポイントのテスト
    
    Requirements: 9.3
    """
    # 検索リクエスト
    response = client.post(
        "/papers/search",
        json={
            "query": "machine learning",
            "max_results": 5
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "papers" in data
    assert "count" in data
    assert isinstance(data["papers"], list)
    assert isinstance(data["count"], int)
    assert data["count"] <= 5


def test_search_papers_validation(client):
    """論文検索のバリデーションテスト
    
    Requirements: 9.3
    """
    # max_resultsが範囲外
    response = client.post(
        "/papers/search",
        json={
            "query": "test",
            "max_results": 200  # 上限は100
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_download_paper_endpoint(client):
    """PDF取得エンドポイントのテスト
    
    Requirements: 9.3
    """
    # 実在する論文をダウンロード
    response = client.post(
        "/papers/download",
        json={
            "arxiv_id": "0704.0001"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert data["arxiv_id"] == "0704.0001"
    assert "pdf_path" in data
    assert "indexed_chunks" in data
    assert data["indexed_chunks"] > 0
    assert "message" in data


def test_rag_query_endpoint(client):
    """RAGクエリエンドポイントのテスト
    
    Requirements: 9.3
    """
    # まず論文をインデックス化
    download_response = client.post(
        "/papers/download",
        json={"arxiv_id": "0704.0001"}
    )
    assert download_response.status_code == 200
    
    # RAGクエリを実行
    response = client.post(
        "/rag/query",
        json={
            "question": "What is this paper about?",
            "arxiv_ids": ["0704.0001"],
            "top_k": 3
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "answer" in data
    assert "sources" in data
    assert "metadata" in data
    assert len(data["answer"]) > 0
    assert isinstance(data["sources"], list)
    assert len(data["sources"]) <= 3


def test_rag_query_without_arxiv_ids(client):
    """arxiv_idsなしのRAGクエリテスト
    
    Requirements: 9.3
    """
    # 論文をインデックス化
    client.post("/papers/download", json={"arxiv_id": "0704.0001"})
    
    # arxiv_idsを指定せずにクエリ
    response = client.post(
        "/rag/query",
        json={
            "question": "What is machine learning?",
            "top_k": 5
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "answer" in data
    assert "sources" in data


def test_rag_query_validation(client):
    """RAGクエリのバリデーションテスト
    
    Requirements: 9.3
    """
    # top_kが範囲外
    response = client.post(
        "/rag/query",
        json={
            "question": "test",
            "top_k": 50  # 上限は20
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_endpoint_workflow(client):
    """エンドポイント間の連携テスト
    
    Requirements: 9.1, 9.2, 9.3
    """
    # 1. ヘルスチェック
    health_response = client.get("/health")
    assert health_response.status_code == 200
    
    # 2. 論文検索
    search_response = client.post(
        "/papers/search",
        json={"query": "attention mechanism", "max_results": 2}
    )
    assert search_response.status_code == 200
    papers = search_response.json()["papers"]
    assert len(papers) > 0
    
    # 3. 最初の論文をダウンロード
    arxiv_id = papers[0]["arxiv_id"]
    download_response = client.post(
        "/papers/download",
        json={"arxiv_id": arxiv_id}
    )
    assert download_response.status_code == 200
    
    # 4. RAGクエリを実行
    rag_response = client.post(
        "/rag/query",
        json={
            "question": "What is the main contribution?",
            "arxiv_ids": [arxiv_id],
            "top_k": 3
        }
    )
    assert rag_response.status_code == 200
    
    # 5. ヘルスチェックでインデックスサイズを確認
    health_response2 = client.get("/health")
    assert health_response2.status_code == 200
    assert health_response2.json()["index_size"] > 0


def test_error_handling_invalid_arxiv_id(client):
    """無効なarXiv IDのエラーハンドリング
    
    Requirements: 9.3
    """
    response = client.post(
        "/papers/download",
        json={"arxiv_id": "invalid_id_12345"}
    )
    
    # エラーが適切に処理されることを確認
    assert response.status_code in [400, 500, 502]


def test_error_handling_empty_index_query(client):
    """空のインデックスでのクエリエラーハンドリング
    
    Requirements: 9.3
    """
    # インデックスが空の状態でRAGクエリ
    response = client.post(
        "/rag/query",
        json={
            "question": "test question",
            "arxiv_ids": ["nonexistent"],
            "top_k": 5
        }
    )
    
    # 空の結果でも正常にレスポンスが返ることを確認
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["sources"]) == 0


def test_concurrent_requests(client):
    """同時リクエストのテスト
    
    Requirements: 9.1, 9.2
    """
    import concurrent.futures
    
    def make_health_request():
        return client.get("/health")
    
    # 10個の同時リクエストを送信
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_health_request) for _ in range(10)]
        responses = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    # すべてのリクエストが成功することを確認
    assert all(r.status_code == 200 for r in responses)


def test_multiple_papers_indexing(client):
    """複数論文のインデックス化テスト
    
    Requirements: 9.3
    """
    arxiv_ids = ["0704.0001", "0704.0002"]
    
    # 複数の論文をインデックス化
    for arxiv_id in arxiv_ids:
        response = client.post(
            "/papers/download",
            json={"arxiv_id": arxiv_id}
        )
        assert response.status_code == 200
    
    # ヘルスチェックでインデックスサイズを確認
    health_response = client.get("/health")
    assert health_response.status_code == 200
    assert health_response.json()["index_size"] > 0
    
    # 全論文を対象にRAGクエリ
    response_all = client.post(
        "/rag/query",
        json={
            "question": "What are these papers about?",
            "top_k": 5
        }
    )
    assert response_all.status_code == 200
    
    # 特定の論文のみを対象にRAGクエリ
    response_filtered = client.post(
        "/rag/query",
        json={
            "question": "What is this paper about?",
            "arxiv_ids": ["0704.0001"],
            "top_k": 5
        }
    )
    assert response_filtered.status_code == 200
    
    # フィルタリングされた結果が全論文対象より少ないことを確認
    sources_all = response_all.json()["sources"]
    sources_filtered = response_filtered.json()["sources"]
    
    # フィルタリングされた結果は指定した論文のみを含む
    for source in sources_filtered:
        assert source["metadata"]["arxiv_id"] == "0704.0001"
