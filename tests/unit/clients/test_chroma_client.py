# -*- coding: utf-8 -*-
"""ChromaClientのユニットテスト

Requirements: 2.2, 2.3, 2.4
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from src.clients.chroma_client import ChromaClient
from src.models.config import ChromaConfig
from src.models.rag import SearchResult


@pytest.fixture
def chroma_config(tmp_path):
    """テスト用Chroma設定"""
    return ChromaConfig(
        collection_name="test_collection",
        persist_dir=tmp_path / "chroma_test",
        distance_metric="cosine"
    )


@pytest.fixture
def chroma_client(chroma_config):
    """ChromaClientインスタンス"""
    return ChromaClient(config=chroma_config)


@pytest.fixture
def sample_embedding():
    """サンプルEmbedding"""
    return [0.1, 0.2, 0.3, 0.4, 0.5]


@pytest.fixture
def sample_metadata():
    """サンプルメタデータ"""
    return {
        "arxiv_id": "2301.00001",
        "title": "Test Paper",
        "authors": ["Author One", "Author Two"],
        "year": 2023,
        "section": "Introduction",
        "chunk_id": "2301.00001_intro_0"
    }


# ========================================
# Initialization tests
# ========================================

def test_chroma_client_initialization(chroma_config):
    """ChromaClientの初期化"""
    client = ChromaClient(config=chroma_config)
    
    assert client.config == chroma_config
    assert client.client is None
    assert client.collection is None


def test_initialize_creates_directories(chroma_client, chroma_config):
    """initialize()でディレクトリが作成される"""
    # 実行
    chroma_client.initialize()
    
    # 検証
    assert chroma_config.persist_dir.exists()
    assert chroma_client.client is not None
    assert chroma_client.collection is not None


def test_initialize_creates_collection(chroma_client):
    """initialize()でコレクションが作成される"""
    # 実行
    chroma_client.initialize()
    
    # 検証
    assert chroma_client.collection.name == "test_collection"
    assert chroma_client.count() == 0


def test_initialize_idempotent(chroma_client):
    """initialize()は複数回呼んでも安全"""
    # 実行
    chroma_client.initialize()
    initial_count = chroma_client.count()
    
    # 再度初期化
    chroma_client.initialize()
    
    # 検証（カウントは変わらない）
    assert chroma_client.count() == initial_count


# ========================================
# add() tests
# ========================================

def test_add_document(chroma_client, sample_embedding, sample_metadata):
    """ドキュメントを追加"""
    chroma_client.initialize()
    
    # 実行
    chroma_client.add(
        embedding=sample_embedding,
        text="This is test text.",
        metadata=sample_metadata,
        chunk_id="test_chunk_1"
    )
    
    # 検証
    assert chroma_client.count() == 1


def test_add_document_with_chunk_id_in_metadata(chroma_client, sample_embedding, sample_metadata):
    """chunk_idをmetadataから取得"""
    chroma_client.initialize()
    
    # 実行（chunk_idを引数で渡さない）
    chroma_client.add(
        embedding=sample_embedding,
        text="This is test text.",
        metadata=sample_metadata
    )
    
    # 検証
    assert chroma_client.count() == 1


def test_add_multiple_documents(chroma_client, sample_embedding, sample_metadata):
    """複数のドキュメントを追加"""
    chroma_client.initialize()
    
    # 実行
    for i in range(3):
        metadata = sample_metadata.copy()
        metadata["chunk_id"] = f"chunk_{i}"
        chroma_client.add(
            embedding=sample_embedding,
            text=f"Text {i}",
            metadata=metadata
        )
    
    # 検証
    assert chroma_client.count() == 3


def test_add_without_initialize_raises_error(chroma_client, sample_embedding, sample_metadata):
    """initialize()前にadd()を呼ぶとエラー"""
    # 実行と検証
    with pytest.raises(RuntimeError, match="Chroma not initialized"):
        chroma_client.add(
            embedding=sample_embedding,
            text="Test",
            metadata=sample_metadata
        )


def test_add_without_chunk_id_raises_error(chroma_client, sample_embedding):
    """chunk_idがない場合はエラー"""
    chroma_client.initialize()
    
    # chunk_idを含まないメタデータ
    metadata = {
        "arxiv_id": "2301.00001",
        "title": "Test"
    }
    
    # 実行と検証
    with pytest.raises(ValueError, match="chunk_id must be provided"):
        chroma_client.add(
            embedding=sample_embedding,
            text="Test",
            metadata=metadata
        )


def test_add_processes_list_metadata(chroma_client, sample_embedding):
    """リスト型のメタデータが文字列に変換される"""
    chroma_client.initialize()
    
    metadata = {
        "chunk_id": "test_chunk",
        "authors": ["Author One", "Author Two"],
        "categories": ["cs.AI", "cs.LG"]
    }
    
    # 実行
    chroma_client.add(
        embedding=sample_embedding,
        text="Test",
        metadata=metadata
    )
    
    # 検証（検索して確認）
    results = chroma_client.search(
        query_embedding=sample_embedding,
        top_k=1
    )
    
    assert len(results) == 1
    assert "Author One, Author Two" in results[0].metadata["authors"]


# ========================================
# search() tests
# ========================================

def test_search_returns_results(chroma_client, sample_embedding, sample_metadata):
    """検索結果が返される"""
    chroma_client.initialize()
    
    # ドキュメントを追加
    chroma_client.add(
        embedding=sample_embedding,
        text="Test document",
        metadata=sample_metadata
    )
    
    # 実行
    results = chroma_client.search(
        query_embedding=sample_embedding,
        top_k=1
    )
    
    # 検証
    assert len(results) == 1
    assert isinstance(results[0], SearchResult)
    assert results[0].text == "Test document"
    assert results[0].score > 0.9  # 同じembeddingなのでスコアは高い


def test_search_with_arxiv_ids_filter(chroma_client, sample_embedding):
    """arxiv_idsでフィルタリング"""
    chroma_client.initialize()
    
    # 異なるarxiv_idで2つのドキュメントを追加
    metadata1 = {
        "chunk_id": "chunk_1",
        "arxiv_id": "2301.00001",
        "title": "Paper 1"
    }
    metadata2 = {
        "chunk_id": "chunk_2",
        "arxiv_id": "2301.00002",
        "title": "Paper 2"
    }
    
    chroma_client.add(sample_embedding, "Text 1", metadata1)
    chroma_client.add(sample_embedding, "Text 2", metadata2)
    
    # 実行（Paper 1のみ検索）
    results = chroma_client.search(
        query_embedding=sample_embedding,
        arxiv_ids=["2301.00001"],
        top_k=10
    )
    
    # 検証
    assert len(results) == 1
    assert results[0].metadata["arxiv_id"] == "2301.00001"


def test_search_with_multiple_arxiv_ids(chroma_client, sample_embedding):
    """複数のarxiv_idsでフィルタリング"""
    chroma_client.initialize()
    
    # 3つのドキュメントを追加
    for i in range(3):
        metadata = {
            "chunk_id": f"chunk_{i}",
            "arxiv_id": f"2301.0000{i}",
            "title": f"Paper {i}"
        }
        chroma_client.add(sample_embedding, f"Text {i}", metadata)
    
    # 実行（Paper 0と2のみ検索）
    results = chroma_client.search(
        query_embedding=sample_embedding,
        arxiv_ids=["2301.00000", "2301.00002"],
        top_k=10
    )
    
    # 検証
    assert len(results) == 2
    arxiv_ids = [r.metadata["arxiv_id"] for r in results]
    assert "2301.00000" in arxiv_ids
    assert "2301.00002" in arxiv_ids
    assert "2301.00001" not in arxiv_ids


def test_search_empty_collection(chroma_client, sample_embedding):
    """空のコレクションで検索"""
    chroma_client.initialize()
    
    # 実行
    results = chroma_client.search(
        query_embedding=sample_embedding,
        top_k=5
    )
    
    # 検証
    assert len(results) == 0


def test_search_top_k_limit(chroma_client, sample_embedding, sample_metadata):
    """top_kで結果数を制限"""
    chroma_client.initialize()
    
    # 10個のドキュメントを追加
    for i in range(10):
        metadata = sample_metadata.copy()
        metadata["chunk_id"] = f"chunk_{i}"
        chroma_client.add(sample_embedding, f"Text {i}", metadata)
    
    # 実行（top_k=3）
    results = chroma_client.search(
        query_embedding=sample_embedding,
        top_k=3
    )
    
    # 検証
    assert len(results) == 3


def test_search_without_initialize_raises_error(chroma_client, sample_embedding):
    """initialize()前にsearch()を呼ぶとエラー"""
    # 実行と検証
    with pytest.raises(RuntimeError, match="Chroma not initialized"):
        chroma_client.search(
            query_embedding=sample_embedding,
            top_k=5
        )


# ========================================
# count() tests
# ========================================

def test_count_empty_collection(chroma_client):
    """空のコレクションのカウント"""
    chroma_client.initialize()
    
    # 実行
    count = chroma_client.count()
    
    # 検証
    assert count == 0


def test_count_after_adding_documents(chroma_client, sample_embedding, sample_metadata):
    """ドキュメント追加後のカウント"""
    chroma_client.initialize()
    
    # 5個追加
    for i in range(5):
        metadata = sample_metadata.copy()
        metadata["chunk_id"] = f"chunk_{i}"
        chroma_client.add(sample_embedding, f"Text {i}", metadata)
    
    # 実行
    count = chroma_client.count()
    
    # 検証
    assert count == 5


def test_count_without_initialize_raises_error(chroma_client):
    """initialize()前にcount()を呼ぶとエラー"""
    # 実行と検証
    with pytest.raises(RuntimeError, match="Chroma not initialized"):
        chroma_client.count()


# ========================================
# reset() tests
# ========================================

def test_reset_clears_collection(chroma_client, sample_embedding, sample_metadata):
    """reset()でコレクションがクリアされる"""
    chroma_client.initialize()
    
    # ドキュメントを追加
    chroma_client.add(sample_embedding, "Test", sample_metadata)
    assert chroma_client.count() == 1
    
    # 実行
    chroma_client.reset()
    
    # 検証
    assert chroma_client.count() == 0


def test_reset_without_initialize_raises_error(chroma_client):
    """initialize()前にreset()を呼ぶとエラー"""
    # 実行と検証
    with pytest.raises(RuntimeError, match="Chroma not initialized"):
        chroma_client.reset()


# ========================================
# _process_metadata() tests
# ========================================

def test_process_metadata_handles_strings(chroma_client):
    """文字列メタデータはそのまま"""
    metadata = {"key": "value"}
    
    # 実行
    processed = chroma_client._process_metadata(metadata)
    
    # 検証
    assert processed["key"] == "value"


def test_process_metadata_handles_numbers(chroma_client):
    """数値メタデータはそのまま"""
    metadata = {"int_key": 42, "float_key": 3.14}
    
    # 実行
    processed = chroma_client._process_metadata(metadata)
    
    # 検証
    assert processed["int_key"] == 42
    assert processed["float_key"] == 3.14


def test_process_metadata_handles_bools(chroma_client):
    """boolメタデータはそのまま"""
    metadata = {"bool_key": True}
    
    # 実行
    processed = chroma_client._process_metadata(metadata)
    
    # 検証
    assert processed["bool_key"] is True


def test_process_metadata_converts_lists(chroma_client):
    """リストは文字列に変換"""
    metadata = {"list_key": ["a", "b", "c"]}
    
    # 実行
    processed = chroma_client._process_metadata(metadata)
    
    # 検証
    assert processed["list_key"] == "a, b, c"


def test_process_metadata_skips_none(chroma_client):
    """Noneはスキップ"""
    metadata = {"key": None}
    
    # 実行
    processed = chroma_client._process_metadata(metadata)
    
    # 検証
    assert "key" not in processed


def test_process_metadata_converts_other_types(chroma_client):
    """その他の型は文字列に変換"""
    metadata = {"dict_key": {"nested": "value"}}
    
    # 実行
    processed = chroma_client._process_metadata(metadata)
    
    # 検証
    assert isinstance(processed["dict_key"], str)


# ========================================
# Error handling tests
# ========================================

def test_initialize_error_handling(chroma_config, tmp_path):
    """initialize()でエラーが発生した場合"""
    # 書き込み不可能なディレクトリを設定
    chroma_config.persist_dir = Path("/invalid/path/that/does/not/exist")
    client = ChromaClient(config=chroma_config)
    
    # 実行と検証
    with pytest.raises(Exception):
        client.initialize()


def test_count_error_propagates(chroma_client):
    """count()でエラーが発生した場合"""
    chroma_client.initialize()
    
    # コレクションを削除してエラーを発生させる
    chroma_client.client.delete_collection(name=chroma_client.config.collection_name)
    chroma_client.collection = None
    
    # 実行と検証
    with pytest.raises(RuntimeError):
        chroma_client.count()


def test_reset_error_propagates(chroma_client):
    """reset()でエラーが発生した場合"""
    chroma_client.initialize()
    
    # clientを無効化
    original_client = chroma_client.client
    chroma_client.client = None
    
    # 実行と検証
    with pytest.raises(RuntimeError):
        chroma_client.reset()
    
    # 復元
    chroma_client.client = original_client
