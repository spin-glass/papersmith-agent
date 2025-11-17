"""RAGService統合テスト"""

import pytest
import pytest_asyncio
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

from src.services.rag_service import RAGService
from src.clients.chroma_client import ChromaClient
from src.services.embedding_service import EmbeddingService
from src.models.config import ChromaConfig, EmbeddingConfig
from src.models.paper import PaperMetadata


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
        collection_name="test_rag_collection",
        distance_metric="cosine"
    )
    client = ChromaClient(config)
    client.initialize()
    return client


@pytest_asyncio.fixture
async def embedding_service(mock_embedding_service):
    """テスト用EmbeddingServiceを作成（モック使用）"""
    # 統合テストでは実際のEmbedding生成は重いのでモックを使用
    return mock_embedding_service


@pytest_asyncio.fixture
async def rag_service(chroma_client, embedding_service):
    """テスト用RAGServiceを作成"""
    return RAGService(
        chroma_client=chroma_client,
        embedding_service=embedding_service
    )


@pytest.fixture
def sample_paper_metadata():
    """サンプル論文メタデータ"""
    return PaperMetadata(
        arxiv_id="2301.00001",
        title="Test Paper on Machine Learning",
        authors=["Author One", "Author Two"],
        abstract="This is a test abstract about machine learning.",
        year=2023,
        categories=["cs.AI", "cs.LG"],
        pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
        published_date=datetime(2023, 1, 1)
    )


@pytest.fixture
def sample_paper_text():
    """サンプル論文テキスト（IMRaD構造）"""
    return """
Abstract

This paper presents a novel approach to machine learning.

1. Introduction

Machine learning has become increasingly important in recent years. 
This work addresses key challenges in the field.

2. Methods

We propose a new algorithm based on neural networks. 
The method uses gradient descent for optimization.

3. Results

Our experiments show significant improvements over baseline methods.
The accuracy increased by 15% on the test dataset.

4. Discussion

The results demonstrate the effectiveness of our approach.
Future work will explore additional applications.

5. Conclusion

We have presented a novel machine learning method.
The approach shows promising results and opens new research directions.

References

[1] Author et al., Previous Work, 2022.
"""


@pytest.mark.asyncio
async def test_rag_service_initialization(rag_service):
    """RAGService初期化のテスト"""
    assert rag_service.chroma is not None
    assert rag_service.embedding is not None


@pytest.mark.asyncio
async def test_index_paper(rag_service, sample_paper_metadata, sample_paper_text):
    """論文インデックス化のテスト"""
    # 論文をインデックス化
    chunk_count = await rag_service.index_paper(
        arxiv_id=sample_paper_metadata.arxiv_id,
        text=sample_paper_text,
        metadata=sample_paper_metadata,
        chunk_size=512
    )
    
    # チャンクが作成されたことを確認
    assert chunk_count > 0
    
    # Chromaにドキュメントが追加されたことを確認
    assert rag_service.chroma.count() == chunk_count


@pytest.mark.asyncio
async def test_query(rag_service, sample_paper_metadata, sample_paper_text):
    """ベクター検索のテスト"""
    # 論文をインデックス化
    await rag_service.index_paper(
        arxiv_id=sample_paper_metadata.arxiv_id,
        text=sample_paper_text,
        metadata=sample_paper_metadata
    )
    
    # 検索を実行
    results = await rag_service.query(
        question="What is the main contribution of this paper?",
        top_k=3
    )
    
    # 結果が返されることを確認
    assert len(results) > 0
    assert len(results) <= 3
    
    # 各結果が必要な属性を持つことを確認
    for result in results:
        assert hasattr(result, "chunk_id")
        assert hasattr(result, "text")
        assert hasattr(result, "score")
        assert hasattr(result, "metadata")
        assert result.metadata["arxiv_id"] == sample_paper_metadata.arxiv_id


@pytest.mark.asyncio
async def test_query_with_arxiv_filter(rag_service, sample_paper_metadata, sample_paper_text):
    """arxiv_idsフィルタ付き検索のテスト"""
    # 複数の論文をインデックス化
    await rag_service.index_paper(
        arxiv_id="2301.00001",
        text=sample_paper_text,
        metadata=sample_paper_metadata
    )
    
    # 別の論文メタデータ
    other_metadata = PaperMetadata(
        arxiv_id="2302.00001",
        title="Another Paper",
        authors=["Author Three"],
        abstract="Different abstract",
        year=2023,
        categories=["cs.CV"],
        pdf_url="https://arxiv.org/pdf/2302.00001.pdf",
        published_date=datetime(2023, 2, 1)
    )
    
    await rag_service.index_paper(
        arxiv_id="2302.00001",
        text="Different paper content about computer vision.",
        metadata=other_metadata
    )
    
    # 特定の論文IDでフィルタリング
    results = await rag_service.query(
        question="What is machine learning?",
        arxiv_ids=["2301.00001"],
        top_k=5
    )
    
    # 指定した論文のチャンクのみが返されることを確認
    assert all(r.metadata["arxiv_id"] == "2301.00001" for r in results)


def test_split_by_imrad(rag_service, sample_paper_text):
    """IMRaD構造分割のテスト"""
    sections = rag_service._split_by_imrad(sample_paper_text)
    
    # セクションが検出されることを確認
    assert len(sections) > 0
    
    # 主要なセクションが含まれることを確認
    section_names = list(sections.keys())
    assert any(name in section_names for name in ["abstract", "introduction", "methods", "results", "conclusion"])


def test_chunk_text(rag_service):
    """テキストチャンク化のテスト"""
    text = "This is sentence one. This is sentence two. This is sentence three. " * 10
    
    chunks = rag_service._chunk_text(text, chunk_size=100)
    
    # チャンクが作成されることを確認
    assert len(chunks) > 0
    
    # 各チャンクがサイズ制限内であることを確認（最後のチャンクを除く）
    for chunk in chunks[:-1]:
        assert len(chunk) <= 100 or " " not in chunk  # 単一の長い単語の場合は例外
    
    # すべてのチャンクを結合すると元のテキストに近いことを確認
    combined = " ".join(chunks)
    assert len(combined) >= len(text) * 0.9  # 多少の空白の違いは許容


def test_chunk_text_empty(rag_service):
    """空テキストのチャンク化テスト"""
    chunks = rag_service._chunk_text("", chunk_size=512)
    assert chunks == []
    
    chunks = rag_service._chunk_text("   ", chunk_size=512)
    assert chunks == []
