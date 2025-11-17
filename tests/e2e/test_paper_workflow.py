# -*- coding: utf-8 -*-
"""論文ワークフローE2Eテスト

Requirements: 1.1, 1.4, 2.1, 2.2, 2.4, 2.5

このテストは実際のAPIエンドポイントを使用して、
検索→ダウンロード→インデックス→質問のフルフローをテストします。
LLMはモックを使用して高速化します。
"""

import pytest
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
    """TestClientを作成
    
    実際のAPIエンドポイントを使用し、LLMはモックを使用します。
    """
    # 環境変数を設定
    with patch.dict("os.environ", {
        "CHROMA_PERSIST_DIR": str(temp_dirs["chroma"]),
        "CHROMA_COLLECTION_NAME": "test_e2e_paper_workflow",
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
def test_full_paper_workflow(client):
    """完全な論文ワークフロー: 検索→ダウンロード→インデックス→質問
    
    Requirements: 1.1, 1.4, 2.1, 2.2, 2.4, 2.5
    
    このテストは以下のフローを検証します:
    1. 論文検索
    2. PDF取得とインデックス化
    3. RAG質問応答
    """
    # 1. ヘルスチェック - システムが起動していることを確認
    health_response = client.get("/health")
    assert health_response.status_code == 200
    health_data = health_response.json()
    assert health_data["status"] in ["ok", "initializing"]
    
    # 2. 論文検索 - キーワードで論文を検索
    search_response = client.post(
        "/papers/search",
        json={
            "query": "transformer attention mechanism",
            "max_results": 3
        }
    )
    assert search_response.status_code == 200
    search_data = search_response.json()
    
    assert "papers" in search_data
    assert "count" in search_data
    assert search_data["count"] > 0
    assert len(search_data["papers"]) > 0
    
    # 最初の論文を選択
    paper = search_data["papers"][0]
    arxiv_id = paper["arxiv_id"]
    
    assert "title" in paper
    assert "authors" in paper
    assert "abstract" in paper
    
    # 3. PDF取得とインデックス化
    download_response = client.post(
        "/papers/download",
        json={"arxiv_id": arxiv_id}
    )
    assert download_response.status_code == 200
    download_data = download_response.json()
    
    assert download_data["status"] == "success"
    assert download_data["arxiv_id"] == arxiv_id
    assert "pdf_path" in download_data
    assert "indexed_chunks" in download_data
    assert download_data["indexed_chunks"] > 0
    
    # 4. インデックスサイズを確認
    health_response2 = client.get("/health")
    assert health_response2.status_code == 200
    health_data2 = health_response2.json()
    assert health_data2["index_size"] > 0
    assert health_data2["index_ready"] is True
    
    # 5. RAG質問応答 - インデックス化された論文に質問
    rag_response = client.post(
        "/rag/query",
        json={
            "question": "What is the main contribution of this paper?",
            "arxiv_ids": [arxiv_id],
            "top_k": 3
        }
    )
    assert rag_response.status_code == 200
    rag_data = rag_response.json()
    
    assert "answer" in rag_data
    assert "sources" in rag_data
    assert "metadata" in rag_data
    
    # 回答が生成されていることを確認
    assert len(rag_data["answer"]) > 0
    
    # ソースが返されていることを確認
    assert len(rag_data["sources"]) > 0
    assert len(rag_data["sources"]) <= 3
    
    # 各ソースが必要な情報を含むことを確認
    for source in rag_data["sources"]:
        assert "chunk_id" in source
        assert "text" in source
        assert "score" in source
        assert "metadata" in source
        assert source["metadata"]["arxiv_id"] == arxiv_id


@pytest.mark.e2e
def test_multiple_papers_workflow(client):
    """複数論文のワークフロー
    
    Requirements: 1.1, 1.4, 2.1, 2.2, 2.4, 2.5
    
    複数の論文をインデックス化し、それらに対して質問を行います。
    """
    # 1. 複数の論文を検索
    search_response = client.post(
        "/papers/search",
        json={
            "query": "deep learning",
            "max_results": 2
        }
    )
    assert search_response.status_code == 200
    papers = search_response.json()["papers"]
    assert len(papers) >= 2
    
    arxiv_ids = [paper["arxiv_id"] for paper in papers[:2]]
    
    # 2. 各論文をダウンロードしてインデックス化
    for arxiv_id in arxiv_ids:
        download_response = client.post(
            "/papers/download",
            json={"arxiv_id": arxiv_id}
        )
        assert download_response.status_code == 200
        assert download_response.json()["status"] == "success"
    
    # 3. インデックスサイズを確認
    health_response = client.get("/health")
    assert health_response.status_code == 200
    assert health_response.json()["index_size"] > 0
    
    # 4. 全論文を対象にRAGクエリ
    rag_response_all = client.post(
        "/rag/query",
        json={
            "question": "What are the main topics of these papers?",
            "top_k": 5
        }
    )
    assert rag_response_all.status_code == 200
    all_sources = rag_response_all.json()["sources"]
    assert len(all_sources) > 0
    
    # 5. 特定の論文のみを対象にRAGクエリ
    rag_response_filtered = client.post(
        "/rag/query",
        json={
            "question": "What is this paper about?",
            "arxiv_ids": [arxiv_ids[0]],
            "top_k": 5
        }
    )
    assert rag_response_filtered.status_code == 200
    filtered_sources = rag_response_filtered.json()["sources"]
    
    # フィルタリングされた結果は指定した論文のみを含む
    for source in filtered_sources:
        assert source["metadata"]["arxiv_id"] == arxiv_ids[0]


@pytest.mark.e2e
def test_workflow_with_specific_paper(client):
    """特定の論文を使用したワークフロー
    
    Requirements: 1.1, 1.4, 2.1, 2.2, 2.4, 2.5
    
    実在する論文IDを使用して、確実にテストが実行できることを確認します。
    """
    # 実在する論文ID
    arxiv_id = "0704.0001"
    
    # 1. PDF取得とインデックス化
    download_response = client.post(
        "/papers/download",
        json={"arxiv_id": arxiv_id}
    )
    assert download_response.status_code == 200
    download_data = download_response.json()
    
    assert download_data["status"] == "success"
    assert download_data["indexed_chunks"] > 0
    
    # 2. 複数の質問を実行
    questions = [
        "What is the main topic of this paper?",
        "What methods are used in this paper?",
        "What are the key findings?"
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
        
        # 各質問に対して回答が生成されることを確認
        assert len(rag_data["answer"]) > 0
        assert len(rag_data["sources"]) > 0


@pytest.mark.e2e
def test_workflow_error_handling(client):
    """ワークフローのエラーハンドリング
    
    Requirements: 1.1, 1.4, 2.1, 2.2, 2.4, 2.5
    
    エラーケースが適切に処理されることを確認します。
    """
    # 1. 無効なarXiv IDでダウンロード
    download_response = client.post(
        "/papers/download",
        json={"arxiv_id": "invalid_id_12345"}
    )
    # エラーが適切に処理されることを確認
    assert download_response.status_code in [400, 500, 502]
    
    # 2. 空のインデックスでRAGクエリ
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
    
    # 3. 無効なパラメータでの検索
    search_response = client.post(
        "/papers/search",
        json={
            "query": "test",
            "max_results": 200  # 上限を超える
        }
    )
    assert search_response.status_code == 422  # Validation error


@pytest.mark.e2e
def test_workflow_with_different_top_k(client):
    """異なるtop_k値でのワークフロー
    
    Requirements: 2.4, 2.5
    
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
    for top_k in [1, 3, 5]:
        rag_response = client.post(
            "/rag/query",
            json={
                "question": "What is this paper about?",
                "arxiv_ids": [arxiv_id],
                "top_k": top_k
            }
        )
        assert rag_response.status_code == 200
        rag_data = rag_response.json()
        
        # ソース数がtop_k以下であることを確認
        assert len(rag_data["sources"]) <= top_k
        assert len(rag_data["sources"]) > 0


@pytest.mark.e2e
def test_workflow_sequential_queries(client):
    """連続したクエリのワークフロー
    
    Requirements: 2.4, 2.5
    
    同じ論文に対して連続してクエリを実行できることを確認します。
    """
    # 論文をインデックス化
    arxiv_id = "0704.0001"
    download_response = client.post(
        "/papers/download",
        json={"arxiv_id": arxiv_id}
    )
    assert download_response.status_code == 200
    
    # 連続して複数のクエリを実行
    for i in range(3):
        rag_response = client.post(
            "/rag/query",
            json={
                "question": f"Question {i+1}: What is discussed in this paper?",
                "arxiv_ids": [arxiv_id],
                "top_k": 3
            }
        )
        assert rag_response.status_code == 200
        rag_data = rag_response.json()
        
        # 各クエリが正常に処理されることを確認
        assert len(rag_data["answer"]) > 0
        assert len(rag_data["sources"]) > 0


@pytest.mark.e2e
def test_workflow_metadata_preservation(client):
    """メタデータの保持を確認するワークフロー
    
    Requirements: 1.4, 2.1, 2.3
    
    論文のメタデータが検索結果に正しく含まれることを確認します。
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
    rag_data = rag_response.json()
    
    # 各ソースが必要なメタデータを持つことを確認
    for source in rag_data["sources"]:
        metadata = source["metadata"]
        assert metadata["arxiv_id"] == arxiv_id
        assert "title" in metadata
        assert "year" in metadata
        assert "section" in metadata
        assert "chunk_id" in metadata
        
        # chunk_idの形式を確認
        assert metadata["chunk_id"].startswith(arxiv_id)
