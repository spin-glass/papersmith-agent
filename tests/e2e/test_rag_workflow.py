# -*- coding: utf-8 -*-
"""RAGワークフローE2Eテスト

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5

このテストは複数論文のインデックス化、複数質問の実行、
フィルタリング機能をテストします。
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
        "CHROMA_COLLECTION_NAME": "test_e2e_rag_workflow",
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
def test_multiple_papers_indexing(client):
    """複数論文のインデックス化
    
    Requirements: 2.1, 2.2, 2.3
    
    複数の論文を順次インデックス化し、すべてが正しく保存されることを確認します。
    """
    # 実在する論文IDを使用
    arxiv_ids = ["0704.0001", "0704.0002"]
    
    # 各論文をインデックス化
    indexed_chunks = {}
    for arxiv_id in arxiv_ids:
        download_response = client.post(
            "/papers/download",
            json={"arxiv_id": arxiv_id}
        )
        assert download_response.status_code == 200
        download_data = download_response.json()
        
        assert download_data["status"] == "success"
        assert download_data["arxiv_id"] == arxiv_id
        assert download_data["indexed_chunks"] > 0
        
        indexed_chunks[arxiv_id] = download_data["indexed_chunks"]
    
    # インデックスサイズを確認
    health_response = client.get("/health")
    assert health_response.status_code == 200
    health_data = health_response.json()
    
    # 全チャンクがインデックス化されていることを確認
    total_chunks = sum(indexed_chunks.values())
    assert health_data["index_size"] == total_chunks
    assert health_data["index_ready"] is True


@pytest.mark.e2e
def test_multiple_questions_execution(client):
    """複数質問の実行
    
    Requirements: 2.4, 2.5
    
    同じ論文セットに対して複数の異なる質問を実行します。
    """
    # 論文をインデックス化
    arxiv_ids = ["0704.0001", "0704.0002"]
    for arxiv_id in arxiv_ids:
        download_response = client.post(
            "/papers/download",
            json={"arxiv_id": arxiv_id}
        )
        assert download_response.status_code == 200
    
    # 複数の質問を実行
    questions = [
        "What is the main topic of these papers?",
        "What methods are discussed?",
        "What are the key contributions?",
        "What datasets are used?",
        "What are the experimental results?"
    ]
    
    for question in questions:
        rag_response = client.post(
            "/rag/query",
            json={
                "question": question,
                "arxiv_ids": arxiv_ids,
                "top_k": 5
            }
        )
        assert rag_response.status_code == 200
        rag_data = rag_response.json()
        
        # 各質問に対して回答が生成されることを確認
        assert "answer" in rag_data
        assert len(rag_data["answer"]) > 0
        
        # ソースが返されることを確認
        assert "sources" in rag_data
        assert len(rag_data["sources"]) > 0
        assert len(rag_data["sources"]) <= 5


@pytest.mark.e2e
def test_filtering_by_arxiv_ids(client):
    """arxiv_idsによるフィルタリング
    
    Requirements: 2.3, 2.4
    
    特定の論文のみを対象にした検索が正しく機能することを確認します。
    """
    # 3つの論文をインデックス化
    arxiv_ids = ["0704.0001", "0704.0002", "1705.05172"]
    
    for arxiv_id in arxiv_ids:
        download_response = client.post(
            "/papers/download",
            json={"arxiv_id": arxiv_id}
        )
        assert download_response.status_code == 200
    
    # 全論文を対象にクエリ
    rag_response_all = client.post(
        "/rag/query",
        json={
            "question": "What is discussed in these papers?",
            "top_k": 10
        }
    )
    assert rag_response_all.status_code == 200
    all_sources = rag_response_all.json()["sources"]
    
    # ソースが返されることを確認（複数論文からの可能性がある）
    assert len(all_sources) > 0
    
    # 特定の1つの論文のみを対象にクエリ
    target_id = arxiv_ids[0]
    rag_response_single = client.post(
        "/rag/query",
        json={
            "question": "What is discussed in this paper?",
            "arxiv_ids": [target_id],
            "top_k": 10
        }
    )
    assert rag_response_single.status_code == 200
    single_sources = rag_response_single.json()["sources"]
    
    # 指定した論文のみからソースが返されることを確認
    for source in single_sources:
        assert source["metadata"]["arxiv_id"] == target_id
    
    # 2つの論文を対象にクエリ
    target_ids = arxiv_ids[:2]
    rag_response_two = client.post(
        "/rag/query",
        json={
            "question": "What is discussed in these papers?",
            "arxiv_ids": target_ids,
            "top_k": 10
        }
    )
    assert rag_response_two.status_code == 200
    two_sources = rag_response_two.json()["sources"]
    
    # 指定した2つの論文のみからソースが返されることを確認
    for source in two_sources:
        assert source["metadata"]["arxiv_id"] in target_ids


@pytest.mark.e2e
def test_filtering_with_different_top_k(client):
    """異なるtop_k値でのフィルタリング
    
    Requirements: 2.4
    
    top_kパラメータとフィルタリングの組み合わせが正しく機能することを確認します。
    """
    # 論文をインデックス化
    arxiv_ids = ["0704.0001", "0704.0002"]
    for arxiv_id in arxiv_ids:
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
                "question": "What is discussed?",
                "arxiv_ids": [arxiv_ids[0]],
                "top_k": top_k
            }
        )
        assert rag_response.status_code == 200
        sources = rag_response.json()["sources"]
        
        # ソース数がtop_k以下であることを確認
        assert len(sources) <= top_k
        
        # すべてのソースが指定した論文からのものであることを確認
        for source in sources:
            assert source["metadata"]["arxiv_id"] == arxiv_ids[0]


@pytest.mark.e2e
def test_rag_workflow_with_sections(client):
    """セクション情報を含むRAGワークフロー
    
    Requirements: 2.1, 2.3, 2.4
    
    IMRaD構造のセクション情報が正しく保持されることを確認します。
    """
    # 論文をインデックス化
    arxiv_id = "0704.0001"
    download_response = client.post(
        "/papers/download",
        json={"arxiv_id": arxiv_id}
    )
    assert download_response.status_code == 200
    
    # セクション関連の質問を実行
    section_questions = [
        ("What is introduced in this paper?", "introduction"),
        ("What methods are used?", "methods"),
        ("What are the results?", "results"),
        ("What is discussed?", "discussion")
    ]
    
    for question, expected_section_hint in section_questions:
        rag_response = client.post(
            "/rag/query",
            json={
                "question": question,
                "arxiv_ids": [arxiv_id],
                "top_k": 5
            }
        )
        assert rag_response.status_code == 200
        sources = rag_response.json()["sources"]
        
        # ソースにセクション情報が含まれることを確認
        for source in sources:
            assert "section" in source["metadata"]
            assert source["metadata"]["section"]  # 空でないことを確認


@pytest.mark.e2e
def test_rag_workflow_concurrent_queries(client):
    """同時クエリのRAGワークフロー
    
    Requirements: 2.4, 2.5
    
    複数のクエリを同時に実行できることを確認します。
    """
    import concurrent.futures
    
    # 論文をインデックス化
    arxiv_ids = ["0704.0001", "0704.0002"]
    for arxiv_id in arxiv_ids:
        download_response = client.post(
            "/papers/download",
            json={"arxiv_id": arxiv_id}
        )
        assert download_response.status_code == 200
    
    # 同時にクエリを実行
    def make_rag_query(question_num):
        return client.post(
            "/rag/query",
            json={
                "question": f"Question {question_num}: What is discussed?",
                "arxiv_ids": arxiv_ids,
                "top_k": 3
            }
        )
    
    # 5つの同時クエリを実行
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_rag_query, i) for i in range(5)]
        responses = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    # すべてのクエリが成功することを確認
    for response in responses:
        assert response.status_code == 200
        rag_data = response.json()
        assert len(rag_data["answer"]) > 0
        assert len(rag_data["sources"]) > 0


@pytest.mark.e2e
def test_rag_workflow_empty_filter(client):
    """空のフィルタでのRAGワークフロー
    
    Requirements: 2.3, 2.4
    
    存在しない論文IDでフィルタリングした場合の動作を確認します。
    """
    # 論文をインデックス化
    arxiv_id = "0704.0001"
    download_response = client.post(
        "/papers/download",
        json={"arxiv_id": arxiv_id}
    )
    assert download_response.status_code == 200
    
    # 存在しない論文IDでフィルタリング
    rag_response = client.post(
        "/rag/query",
        json={
            "question": "What is discussed?",
            "arxiv_ids": ["nonexistent_paper_id"],
            "top_k": 5
        }
    )
    assert rag_response.status_code == 200
    rag_data = rag_response.json()
    
    # 空の結果が返されることを確認
    assert len(rag_data["sources"]) == 0
    
    # 回答は生成される（空のコンテキストでも）
    assert "answer" in rag_data


@pytest.mark.e2e
def test_rag_workflow_metadata_consistency(client):
    """メタデータの一貫性を確認するRAGワークフロー
    
    Requirements: 2.1, 2.3, 2.4
    
    複数の論文をインデックス化し、各論文のメタデータが正しく保持されることを確認します。
    """
    # 複数の論文をインデックス化
    arxiv_ids = ["0704.0001", "0704.0002"]
    paper_metadata = {}
    
    for arxiv_id in arxiv_ids:
        download_response = client.post(
            "/papers/download",
            json={"arxiv_id": arxiv_id}
        )
        assert download_response.status_code == 200
        paper_metadata[arxiv_id] = download_response.json()
    
    # 各論文に対してクエリを実行し、メタデータを確認
    for arxiv_id in arxiv_ids:
        rag_response = client.post(
            "/rag/query",
            json={
                "question": "What is this paper about?",
                "arxiv_ids": [arxiv_id],
                "top_k": 5
            }
        )
        assert rag_response.status_code == 200
        sources = rag_response.json()["sources"]
        
        # 各ソースのメタデータを確認
        for source in sources:
            metadata = source["metadata"]
            
            # 基本的なメタデータが含まれることを確認
            assert metadata["arxiv_id"] == arxiv_id
            assert "title" in metadata
            assert "year" in metadata
            assert "section" in metadata
            assert "chunk_id" in metadata
            
            # chunk_idの形式を確認
            assert metadata["chunk_id"].startswith(arxiv_id)


@pytest.mark.e2e
def test_rag_workflow_large_result_set(client):
    """大きな結果セットのRAGワークフロー
    
    Requirements: 2.4, 2.5
    
    多くのチャンクを持つ論文に対してクエリを実行します。
    """
    # 論文をインデックス化
    arxiv_id = "0704.0001"
    download_response = client.post(
        "/papers/download",
        json={"arxiv_id": arxiv_id}
    )
    assert download_response.status_code == 200
    download_data = download_response.json()
    
    # 多くのチャンクがインデックス化されていることを確認
    assert download_data["indexed_chunks"] > 10
    
    # 大きなtop_k値でクエリ
    rag_response = client.post(
        "/rag/query",
        json={
            "question": "What is discussed in this paper?",
            "arxiv_ids": [arxiv_id],
            "top_k": 20
        }
    )
    assert rag_response.status_code == 200
    rag_data = rag_response.json()
    
    # 結果が返されることを確認
    assert len(rag_data["sources"]) > 0
    assert len(rag_data["sources"]) <= 20
    
    # 回答が生成されることを確認
    assert len(rag_data["answer"]) > 0


@pytest.mark.e2e
def test_rag_workflow_question_variations(client):
    """質問のバリエーションを含むRAGワークフロー
    
    Requirements: 2.4, 2.5
    
    異なるタイプの質問に対して適切に応答することを確認します。
    """
    # 論文をインデックス化
    arxiv_id = "0704.0001"
    download_response = client.post(
        "/papers/download",
        json={"arxiv_id": arxiv_id}
    )
    assert download_response.status_code == 200
    
    # 異なるタイプの質問
    question_types = [
        "What is the main topic?",  # 概要質問
        "How does the method work?",  # 手法質問
        "What are the results?",  # 結果質問
        "Why is this important?",  # 重要性質問
        "What are the limitations?",  # 制限質問
    ]
    
    for question in question_types:
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
        
        # 各質問タイプに対して回答が生成されることを確認
        assert len(rag_data["answer"]) > 0
        assert len(rag_data["sources"]) > 0


@pytest.mark.e2e
def test_rag_workflow_incremental_indexing(client):
    """段階的なインデックス化のRAGワークフロー
    
    Requirements: 2.1, 2.2, 2.3, 2.4
    
    論文を1つずつ追加し、各段階でクエリが正しく機能することを確認します。
    """
    arxiv_ids = ["0704.0001", "0704.0002", "1705.05172"]
    
    for i, arxiv_id in enumerate(arxiv_ids):
        # 論文をインデックス化
        download_response = client.post(
            "/papers/download",
            json={"arxiv_id": arxiv_id}
        )
        assert download_response.status_code == 200
        
        # インデックスサイズを確認
        health_response = client.get("/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["index_size"] > 0
        
        # 現在までにインデックス化された論文を対象にクエリ
        current_ids = arxiv_ids[:i+1]
        rag_response = client.post(
            "/rag/query",
            json={
                "question": "What are these papers about?",
                "arxiv_ids": current_ids,
                "top_k": 5
            }
        )
        assert rag_response.status_code == 200
        rag_data = rag_response.json()
        
        # 回答が生成されることを確認
        assert len(rag_data["answer"]) > 0
        assert len(rag_data["sources"]) > 0
        
        # ソースが現在の論文セットからのみであることを確認
        for source in rag_data["sources"]:
            assert source["metadata"]["arxiv_id"] in current_ids
