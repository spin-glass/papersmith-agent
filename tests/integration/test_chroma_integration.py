"""Chroma統合テスト

Requirements: 2.2, 2.3, 2.4
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.clients.chroma_client import ChromaClient
from src.models.config import ChromaConfig


@pytest.fixture
def temp_chroma_dir():
    """一時的なChromaディレクトリを作成"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # クリーンアップ
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def chroma_client(temp_chroma_dir):
    """テスト用ChromaClientを作成"""
    config = ChromaConfig(
        persist_dir=temp_chroma_dir,
        collection_name="test_collection",
        distance_metric="cosine"
    )
    client = ChromaClient(config)
    client.initialize()
    return client


def test_chroma_initialize(temp_chroma_dir):
    """Chroma初期化のテスト"""
    config = ChromaConfig(
        persist_dir=temp_chroma_dir,
        collection_name="test_collection"
    )
    client = ChromaClient(config)
    client.initialize()
    
    assert client.client is not None
    assert client.collection is not None
    assert client.count() == 0


def test_chroma_add_document(chroma_client):
    """ドキュメント追加のテスト"""
    # テストデータ
    embedding = [0.1] * 768  # 768次元のダミーEmbedding
    text = "This is a test document about machine learning."
    metadata = {
        "arxiv_id": "2301.00001",
        "title": "Test Paper",
        "authors": ["Author One", "Author Two"],
        "year": 2023,
        "section": "introduction",
        "chunk_id": "2301.00001_introduction_0"
    }
    
    # ドキュメントを追加
    chroma_client.add(
        embedding=embedding,
        text=text,
        metadata=metadata
    )
    
    # カウントを確認
    assert chroma_client.count() == 1


def test_chroma_search(chroma_client):
    """ベクター検索のテスト"""
    # テストデータを追加
    embeddings = [
        [0.1] * 768,
        [0.2] * 768,
        [0.3] * 768
    ]
    texts = [
        "Machine learning is a subset of AI.",
        "Deep learning uses neural networks.",
        "Natural language processing handles text."
    ]
    metadatas = [
        {
            "arxiv_id": "2301.00001",
            "title": "ML Paper",
            "authors": "Author One",
            "year": 2023,
            "section": "introduction",
            "chunk_id": "2301.00001_introduction_0"
        },
        {
            "arxiv_id": "2301.00001",
            "title": "ML Paper",
            "authors": "Author One",
            "year": 2023,
            "section": "methods",
            "chunk_id": "2301.00001_methods_0"
        },
        {
            "arxiv_id": "2302.00001",
            "title": "NLP Paper",
            "authors": "Author Two",
            "year": 2023,
            "section": "introduction",
            "chunk_id": "2302.00001_introduction_0"
        }
    ]
    
    for emb, txt, meta in zip(embeddings, texts, metadatas):
        chroma_client.add(embedding=emb, text=txt, metadata=meta)
    
    # 検索を実行
    query_embedding = [0.15] * 768
    results = chroma_client.search(
        query_embedding=query_embedding,
        top_k=2
    )
    
    assert len(results) == 2
    assert all(hasattr(r, "chunk_id") for r in results)
    assert all(hasattr(r, "text") for r in results)
    assert all(hasattr(r, "score") for r in results)
    assert all(hasattr(r, "metadata") for r in results)


def test_chroma_search_with_filter(chroma_client):
    """arxiv_idsフィルタ付き検索のテスト"""
    # テストデータを追加
    embeddings = [
        [0.1] * 768,
        [0.2] * 768,
        [0.3] * 768
    ]
    texts = [
        "Paper 1 content",
        "Paper 1 more content",
        "Paper 2 content"
    ]
    metadatas = [
        {
            "arxiv_id": "2301.00001",
            "title": "Paper 1",
            "authors": "Author One",
            "year": 2023,
            "section": "introduction",
            "chunk_id": "2301.00001_introduction_0"
        },
        {
            "arxiv_id": "2301.00001",
            "title": "Paper 1",
            "authors": "Author One",
            "year": 2023,
            "section": "methods",
            "chunk_id": "2301.00001_methods_0"
        },
        {
            "arxiv_id": "2302.00001",
            "title": "Paper 2",
            "authors": "Author Two",
            "year": 2023,
            "section": "introduction",
            "chunk_id": "2302.00001_introduction_0"
        }
    ]
    
    for emb, txt, meta in zip(embeddings, texts, metadatas):
        chroma_client.add(embedding=emb, text=txt, metadata=meta)
    
    # 特定の論文IDでフィルタリング
    query_embedding = [0.15] * 768
    results = chroma_client.search(
        query_embedding=query_embedding,
        arxiv_ids=["2301.00001"],
        top_k=5
    )
    
    # Paper 1のチャンクのみが返されることを確認
    assert len(results) == 2
    assert all(r.metadata["arxiv_id"] == "2301.00001" for r in results)


def test_chroma_count(chroma_client):
    """ドキュメント数カウントのテスト"""
    assert chroma_client.count() == 0
    
    # ドキュメントを追加
    for i in range(5):
        chroma_client.add(
            embedding=[0.1] * 768,
            text=f"Document {i}",
            metadata={
                "arxiv_id": f"230{i}.00001",
                "title": f"Paper {i}",
                "authors": "Author",
                "year": 2023,
                "section": "introduction",
                "chunk_id": f"230{i}.00001_introduction_0"
            }
        )
    
    assert chroma_client.count() == 5


def test_chroma_persistence(temp_chroma_dir):
    """永続化のテスト
    
    Requirements: 2.2, 2.3
    """
    # 最初のクライアントでデータを追加
    config1 = ChromaConfig(
        persist_dir=temp_chroma_dir,
        collection_name="test_persistence",
        distance_metric="cosine"
    )
    client1 = ChromaClient(config1)
    client1.initialize()
    
    # テストデータを追加
    test_data = [
        {
            "embedding": [0.1] * 768,
            "text": "First document about machine learning",
            "metadata": {
                "arxiv_id": "2301.00001",
                "title": "ML Paper",
                "authors": "Author One",
                "year": 2023,
                "section": "introduction",
                "chunk_id": "2301.00001_introduction_0"
            }
        },
        {
            "embedding": [0.2] * 768,
            "text": "Second document about deep learning",
            "metadata": {
                "arxiv_id": "2301.00002",
                "title": "DL Paper",
                "authors": "Author Two",
                "year": 2023,
                "section": "methods",
                "chunk_id": "2301.00002_methods_0"
            }
        }
    ]
    
    for data in test_data:
        client1.add(**data)
    
    initial_count = client1.count()
    assert initial_count == 2
    
    # 2つ目のクライアントで同じディレクトリから読み込み
    config2 = ChromaConfig(
        persist_dir=temp_chroma_dir,
        collection_name="test_persistence",
        distance_metric="cosine"
    )
    client2 = ChromaClient(config2)
    client2.initialize()
    
    # データが永続化されていることを確認
    assert client2.count() == initial_count
    
    # 検索が正常に動作することを確認
    query_embedding = [0.15] * 768
    results = client2.search(
        query_embedding=query_embedding,
        top_k=2
    )
    
    assert len(results) == 2
    assert all(hasattr(r, "chunk_id") for r in results)
    assert all(hasattr(r, "text") for r in results)


def test_chroma_large_dataset(temp_chroma_dir):
    """大量データのテスト
    
    Requirements: 2.2, 2.3
    """
    config = ChromaConfig(
        persist_dir=temp_chroma_dir,
        collection_name="test_large_dataset",
        distance_metric="cosine"
    )
    client = ChromaClient(config)
    client.initialize()
    
    # 100個のドキュメントを追加
    num_docs = 100
    for i in range(num_docs):
        client.add(
            embedding=[float(i % 10) / 10.0] * 768,
            text=f"Document {i} with content about topic {i % 10}",
            metadata={
                "arxiv_id": f"23{i:02d}.00001",
                "title": f"Paper {i}",
                "authors": f"Author {i}",
                "year": 2023,
                "section": "introduction",
                "chunk_id": f"23{i:02d}.00001_introduction_0"
            }
        )
    
    # カウントを確認
    assert client.count() == num_docs
    
    # 検索が正常に動作することを確認
    query_embedding = [0.5] * 768
    results = client.search(
        query_embedding=query_embedding,
        top_k=10
    )
    
    assert len(results) == 10
    assert all(hasattr(r, "chunk_id") for r in results)
    assert all(hasattr(r, "score") for r in results)
    
    # スコアが降順にソートされていることを確認
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_chroma_multiple_collections(temp_chroma_dir):
    """複数コレクションのテスト
    
    Requirements: 2.2, 2.3
    """
    # コレクション1
    config1 = ChromaConfig(
        persist_dir=temp_chroma_dir,
        collection_name="collection_1",
        distance_metric="cosine"
    )
    client1 = ChromaClient(config1)
    client1.initialize()
    
    client1.add(
        embedding=[0.1] * 768,
        text="Document in collection 1",
        metadata={
            "arxiv_id": "2301.00001",
            "title": "Paper 1",
            "authors": "Author",
            "year": 2023,
            "section": "introduction",
            "chunk_id": "2301.00001_introduction_0"
        }
    )
    
    # コレクション2
    config2 = ChromaConfig(
        persist_dir=temp_chroma_dir,
        collection_name="collection_2",
        distance_metric="cosine"
    )
    client2 = ChromaClient(config2)
    client2.initialize()
    
    client2.add(
        embedding=[0.2] * 768,
        text="Document in collection 2",
        metadata={
            "arxiv_id": "2302.00001",
            "title": "Paper 2",
            "authors": "Author",
            "year": 2023,
            "section": "introduction",
            "chunk_id": "2302.00001_introduction_0"
        }
    )
    
    # 各コレクションが独立していることを確認
    assert client1.count() == 1
    assert client2.count() == 1
    
    # 各コレクションで検索が正常に動作することを確認
    query_embedding = [0.15] * 768
    
    results1 = client1.search(query_embedding=query_embedding, top_k=5)
    assert len(results1) == 1
    assert results1[0].metadata["arxiv_id"] == "2301.00001"
    
    results2 = client2.search(query_embedding=query_embedding, top_k=5)
    assert len(results2) == 1
    assert results2[0].metadata["arxiv_id"] == "2302.00001"


def test_chroma_batch_operations(temp_chroma_dir):
    """バッチ操作のテスト
    
    Requirements: 2.2, 2.3
    """
    config = ChromaConfig(
        persist_dir=temp_chroma_dir,
        collection_name="test_batch",
        distance_metric="cosine"
    )
    client = ChromaClient(config)
    client.initialize()
    
    # バッチでドキュメントを追加
    batch_size = 20
    for i in range(batch_size):
        client.add(
            embedding=[float(i) / batch_size] * 768,
            text=f"Batch document {i}",
            metadata={
                "arxiv_id": f"23{i:02d}.00001",
                "title": f"Batch Paper {i}",
                "authors": "Batch Author",
                "year": 2023,
                "section": "introduction",
                "chunk_id": f"23{i:02d}.00001_introduction_0"
            }
        )
    
    # すべてのドキュメントが追加されたことを確認
    assert client.count() == batch_size
    
    # 検索が正常に動作することを確認
    query_embedding = [0.5] * 768
    results = client.search(
        query_embedding=query_embedding,
        top_k=5
    )
    
    assert len(results) == 5


def test_chroma_distance_metrics(temp_chroma_dir):
    """距離メトリクスのテスト
    
    Requirements: 2.2
    """
    # cosine距離でテスト
    config_cosine = ChromaConfig(
        persist_dir=temp_chroma_dir,
        collection_name="test_cosine",
        distance_metric="cosine"
    )
    client_cosine = ChromaClient(config_cosine)
    client_cosine.initialize()
    
    # テストデータを追加
    client_cosine.add(
        embedding=[1.0, 0.0] + [0.0] * 766,
        text="Document with specific embedding",
        metadata={
            "arxiv_id": "2301.00001",
            "title": "Test Paper",
            "authors": "Author",
            "year": 2023,
            "section": "introduction",
            "chunk_id": "2301.00001_introduction_0"
        }
    )
    
    # 検索が正常に動作することを確認
    query_embedding = [0.9, 0.1] + [0.0] * 766
    results = client_cosine.search(
        query_embedding=query_embedding,
        top_k=1
    )
    
    assert len(results) == 1
    assert results[0].score >= 0
