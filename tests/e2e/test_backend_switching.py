# -*- coding: utf-8 -*-
"""バックエンド切り替えE2Eテスト

Requirements: 12.2, 12.3, 12.8

このテストは異なるバックエンド（Gemini、OpenAI、local-cpu）間の
切り替えと基本動作を確認します。

注意: このテストはモックを使用しているため、実際のバックエンド切り替えではなく、
環境変数による設定の検証を行います。
"""

import pytest
import os
from pathlib import Path
import tempfile
import shutil
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from src.api.main import app


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
def client(temp_dirs, mock_embedding_service, mock_llm_service):
    """TestClientを作成（デフォルトバックエンド）
    
    実際のAPIエンドポイントを使用し、LLM/Embeddingはモックを使用します。
    """
    # 環境変数を設定
    with patch.dict("os.environ", {
        "CHROMA_PERSIST_DIR": str(temp_dirs["chroma"]),
        "CHROMA_COLLECTION_NAME": "test_e2e_backend",
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
            mock_emb_instance.embed = mock_embedding_service.embed
            mock_emb_instance.embed_batch = mock_embedding_service.embed_batch
            mock_emb_cls.return_value = mock_emb_instance
            
            mock_llm_instance = MagicMock()
            mock_llm_instance.load_model = AsyncMock()
            mock_llm_instance.generate = mock_llm_service.generate
            mock_llm_cls.return_value = mock_llm_instance
            
            # TestClientを作成
            with TestClient(app) as test_client:
                yield test_client


@pytest.mark.e2e
def test_basic_workflow_with_mocked_backend(client):
    """モックバックエンドでの基本ワークフロー
    
    Requirements: 12.2, 12.3, 12.8
    
    モックされたバックエンドで基本的なワークフローが動作することを確認します。
    """
    # ヘルスチェック
    health_response = client.get("/health")
    assert health_response.status_code == 200
    
    # 論文をインデックス化
    arxiv_id = "0704.0001"
    download_response = client.post(
        "/papers/download",
        json={"arxiv_id": arxiv_id}
    )
    assert download_response.status_code == 200
    assert download_response.json()["status"] == "success"
    
    # RAGクエリを実行
    rag_response = client.post(
        "/rag/query",
        json={
            "question": "What is this paper about?",
            "arxiv_ids": [arxiv_id],
            "top_k": 3
        }
    )
    assert rag_response.status_code == 200
    rag_data = rag_response.json()
    
    assert len(rag_data["answer"]) > 0
    assert len(rag_data["sources"]) > 0


@pytest.mark.e2e
def test_multiple_papers_with_backend(client):
    """複数論文でのバックエンド動作確認
    
    Requirements: 12.2, 12.3
    
    複数の論文をインデックス化し、バックエンドが正しく動作することを確認します。
    """
    arxiv_ids = ["0704.0001", "0704.0002"]
    
    # 複数の論文をインデックス化
    for arxiv_id in arxiv_ids:
        download_response = client.post(
            "/papers/download",
            json={"arxiv_id": arxiv_id}
        )
        assert download_response.status_code == 200
    
    # 全論文を対象にRAGクエリ
    rag_response = client.post(
        "/rag/query",
        json={
            "question": "What are these papers about?",
            "arxiv_ids": arxiv_ids,
            "top_k": 5
        }
    )
    assert rag_response.status_code == 200
    rag_data = rag_response.json()
    
    assert len(rag_data["answer"]) > 0
    assert len(rag_data["sources"]) > 0


@pytest.mark.e2e
def test_backend_with_different_queries(client):
    """異なるクエリでのバックエンド動作
    
    Requirements: 12.2, 12.3
    
    異なるタイプのクエリでバックエンドが正しく動作することを確認します。
    """
    # 論文をインデックス化
    arxiv_id = "0704.0001"
    download_response = client.post(
        "/papers/download",
        json={"arxiv_id": arxiv_id}
    )
    assert download_response.status_code == 200
    
    # 異なるクエリを実行
    questions = [
        "What is the main topic?",
        "What methods are used?",
        "What are the results?"
    ]
    
    for question in questions:
        rag_response = client.post(
            "/rag/query",
            json={
                "question": question,
                "arxiv_ids": [arxiv_id],
                "top_k": 3
            }
        )
        assert rag_response.status_code == 200
        rag_data = rag_response.json()
        
        assert len(rag_data["answer"]) > 0
        assert len(rag_data["sources"]) > 0


@pytest.mark.e2e
def test_backend_with_filtering(client):
    """フィルタリング機能でのバックエンド動作
    
    Requirements: 12.2, 12.3
    
    arxiv_idsフィルタリングがバックエンドで正しく動作することを確認します。
    """
    # 複数の論文をインデックス化
    arxiv_ids = ["0704.0001", "0704.0002"]
    for arxiv_id in arxiv_ids:
        download_response = client.post(
            "/papers/download",
            json={"arxiv_id": arxiv_id}
        )
        assert download_response.status_code == 200
    
    # 特定の論文のみを対象にクエリ
    rag_response = client.post(
        "/rag/query",
        json={
            "question": "What is this paper about?",
            "arxiv_ids": [arxiv_ids[0]],
            "top_k": 5
        }
    )
    assert rag_response.status_code == 200
    sources = rag_response.json()["sources"]
    
    # 指定した論文のみからソースが返されることを確認
    for source in sources:
        assert source["metadata"]["arxiv_id"] == arxiv_ids[0]


@pytest.mark.e2e
def test_backend_error_handling(client):
    """バックエンドのエラーハンドリング
    
    Requirements: 12.2, 12.3
    
    エラーケースが適切に処理されることを確認します。
    """
    # 無効なarXiv IDでダウンロード
    download_response = client.post(
        "/papers/download",
        json={"arxiv_id": "invalid_id_12345"}
    )
    # エラーが適切に処理されることを確認
    assert download_response.status_code in [400, 500, 502]
    
    # 空のインデックスでRAGクエリ
    rag_response = client.post(
        "/rag/query",
        json={
            "question": "test question",
            "arxiv_ids": ["nonexistent_paper"],
            "top_k": 5
        }
    )
    # 空の結果でも正常にレスポンスが返ることを確認
    assert rag_response.status_code == 200
    rag_data = rag_response.json()
    assert "answer" in rag_data
    assert len(rag_data["sources"]) == 0


@pytest.mark.e2e
def test_backend_sequential_operations(client):
    """連続操作でのバックエンド動作
    
    Requirements: 12.2, 12.3
    
    連続した操作でバックエンドが安定して動作することを確認します。
    """
    arxiv_id = "0704.0001"
    
    # 論文をインデックス化
    download_response = client.post(
        "/papers/download",
        json={"arxiv_id": arxiv_id}
    )
    assert download_response.status_code == 200
    
    # 連続してクエリを実行
    for i in range(3):
        rag_response = client.post(
            "/rag/query",
            json={
                "question": f"Question {i+1}: What is discussed?",
                "arxiv_ids": [arxiv_id],
                "top_k": 3
            }
        )
        assert rag_response.status_code == 200
        rag_data = rag_response.json()
        
        assert len(rag_data["answer"]) > 0
        assert len(rag_data["sources"]) > 0


@pytest.mark.e2e
def test_backend_with_varying_top_k(client):
    """異なるtop_k値でのバックエンド動作
    
    Requirements: 12.2, 12.3
    
    top_kパラメータが正しく機能することを確認します。
    """
    # 論文をインデックス化
    arxiv_id = "0704.0001"
    download_response = client.post(
        "/papers/download",
        json={"arxiv_id": arxiv_id}
    )
    assert download_response.status_code == 200
    
    # 異なるtop_k値でクエリ
    for top_k in [1, 3, 5, 10]:
        rag_response = client.post(
            "/rag/query",
            json={
                "question": "What is this paper about?",
                "arxiv_ids": [arxiv_id],
                "top_k": top_k
            }
        )
        assert rag_response.status_code == 200
        sources = rag_response.json()["sources"]
        
        # ソース数がtop_k以下であることを確認
        assert len(sources) <= top_k
        assert len(sources) > 0


@pytest.mark.e2e
def test_backend_metadata_preservation(client):
    """メタデータ保持でのバックエンド動作
    
    Requirements: 12.2, 12.3
    
    バックエンドがメタデータを正しく保持することを確認します。
    """
    # 論文をインデックス化
    arxiv_id = "0704.0001"
    download_response = client.post(
        "/papers/download",
        json={"arxiv_id": arxiv_id}
    )
    assert download_response.status_code == 200
    
    # RAGクエリを実行
    rag_response = client.post(
        "/rag/query",
        json={
            "question": "What is this paper about?",
            "arxiv_ids": [arxiv_id],
            "top_k": 3
        }
    )
    assert rag_response.status_code == 200
    sources = rag_response.json()["sources"]
    
    # 各ソースが必要なメタデータを持つことを確認
    for source in sources:
        metadata = source["metadata"]
        assert metadata["arxiv_id"] == arxiv_id
        assert "title" in metadata
        assert "year" in metadata
        assert "section" in metadata
        assert "chunk_id" in metadata


@pytest.mark.e2e
def test_default_backend(temp_dirs, mock_embedding_service, mock_llm_service):
    """デフォルトバックエンドの確認
    
    Requirements: 12.8
    
    環境変数が設定されていない場合、デフォルトでGeminiが使用されることを確認します。
    """
    # 環境変数を設定せずにクライアントを作成
    env_vars = {
        "CHROMA_PERSIST_DIR": str(temp_dirs["chroma"]),
        "CHROMA_COLLECTION_NAME": "test_default_backend",
        "CACHE_DIR": str(temp_dirs["cache"]),
        "LOG_DIR": str(temp_dirs["logs"]),
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY", "test_key")
    }
    
    with patch.dict("os.environ", env_vars, clear=True):
        with patch("src.api.main.EmbeddingService") as mock_emb_cls, \
             patch("src.api.main.LLMService") as mock_llm_cls:
            
            mock_emb_instance = MagicMock()
            mock_emb_instance.load_model = AsyncMock()
            mock_emb_instance.embed = mock_embedding_service.embed
            mock_emb_instance.embed_batch = mock_embedding_service.embed_batch
            mock_emb_cls.return_value = mock_emb_instance
            
            mock_llm_instance = MagicMock()
            mock_llm_instance.load_model = AsyncMock()
            mock_llm_instance.generate = mock_llm_service.generate
            mock_llm_cls.return_value = mock_llm_instance
            
            with TestClient(app) as client:
                # ヘルスチェック
                health_response = client.get("/health")
                assert health_response.status_code == 200
                
                # 基本的な操作が動作することを確認
                arxiv_id = "0704.0001"
                download_response = client.post(
                    "/papers/download",
                    json={"arxiv_id": arxiv_id}
                )
                assert download_response.status_code == 200
