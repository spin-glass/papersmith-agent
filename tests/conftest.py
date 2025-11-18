# -*- coding: utf-8 -*-
"""共通テストフィクスチャ

Requirements: Testing Strategy - Test Fixtures
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Debug: Print sys.path
print(f"DEBUG: project_root = {project_root}")
print(f"DEBUG: sys.path = {sys.path}")

import pytest
from datetime import datetime
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock

from src.models.paper import PaperMetadata
from src.models.rag import SearchResult, RAGResponse
from src.models.config import ChromaConfig, LLMConfig, EmbeddingConfig


@pytest.fixture
def sample_paper_metadata() -> PaperMetadata:
    """サンプル論文メタデータフィクスチャ
    
    Returns:
        テスト用の論文メタデータ
    """
    return PaperMetadata(
        arxiv_id="2301.00001",
        title="Example Paper: A Novel Approach to Machine Learning",
        authors=["Alice Smith", "Bob Johnson", "Carol Williams"],
        abstract="This paper presents a novel approach to machine learning that improves accuracy by 15%.",
        year=2023,
        categories=["cs.AI", "cs.LG"],
        pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
        doi="10.1234/example.2023.00001",
        published_date=datetime(2023, 1, 1, 0, 0, 0)
    )


@pytest.fixture
def sample_search_results() -> List[SearchResult]:
    """サンプル検索結果フィクスチャ
    
    Returns:
        テスト用の検索結果リスト
    """
    return [
        SearchResult(
            chunk_id="2301.00001_introduction_0",
            text="This paper presents a novel approach to machine learning.",
            score=0.85,
            metadata={
                "arxiv_id": "2301.00001",
                "title": "Example Paper",
                "authors": "Alice Smith, Bob Johnson",
                "year": 2023,
                "section": "introduction"
            }
        ),
        SearchResult(
            chunk_id="2301.00001_methods_0",
            text="We propose a new algorithm that combines deep learning with reinforcement learning.",
            score=0.78,
            metadata={
                "arxiv_id": "2301.00001",
                "title": "Example Paper",
                "authors": "Alice Smith, Bob Johnson",
                "year": 2023,
                "section": "methods"
            }
        )
    ]


@pytest.fixture
def chroma_client():
    """In-memory Chromaクライアントフィクスチャ
    
    テスト用のin-memoryベクターストアを提供します。
    
    Returns:
        モックChromaクライアント
    """
    from src.clients.chroma_client import ChromaClient
    
    # In-memory設定
    config = ChromaConfig(
        persist_directory=":memory:",
        collection_name="test_collection"
    )
    
    client = ChromaClient(config)
    client.initialize()
    
    yield client
    
    # クリーンアップ
    try:
        client.client.delete_collection(name=config.collection_name)
    except Exception:
        pass


@pytest.fixture
def mock_llm_service():
    """モックLLMサービスフィクスチャ
    
    LLMサービスのモックを提供します。
    実際のLLM呼び出しを避けてテストを高速化します。
    
    Returns:
        モックLLMサービス
    """
    mock_service = MagicMock()
    mock_service._is_loaded = True
    mock_service.backend = {"type": "mock"}
    
    # デフォルトの回答を設定
    async def mock_generate(question: str, context: str, **kwargs) -> str:
        return f"これは{question}に対するテスト回答です。コンテキスト: {context[:50]}..."
    
    mock_service.generate = mock_generate
    mock_service.is_loaded = MagicMock(return_value=True)
    mock_service.get_model_name = MagicMock(return_value="mock:test-model")
    
    return mock_service


@pytest.fixture
def mock_embedding_service():
    """モックEmbeddingサービスフィクスチャ
    
    Embeddingサービスのモックを提供します。
    実際のEmbedding生成を避けてテストを高速化します。
    
    Returns:
        モックEmbeddingサービス
    """
    mock_service = MagicMock()
    mock_service._is_loaded = True
    mock_service.backend = {"type": "mock"}
    
    # デフォルトのEmbeddingを設定（768次元）
    async def mock_embed(text: str) -> List[float]:
        # テキストのハッシュから決定的なEmbeddingを生成
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        return [(hash_val % 1000) / 1000.0] * 768
    
    async def mock_embed_batch(texts: List[str]) -> List[List[float]]:
        return [await mock_embed(text) for text in texts]
    
    mock_service.embed = mock_embed
    mock_service.embed_batch = mock_embed_batch
    mock_service.is_loaded = MagicMock(return_value=True)
    mock_service.get_embedding_dimension = MagicMock(return_value=768)
    
    return mock_service


@pytest.fixture
def mock_paper_service():
    """モックPaperサービスフィクスチャ
    
    PaperServiceのモックを提供します。
    実際のAPI呼び出しを避けてテストを高速化します。
    
    Returns:
        モックPaperサービス
    """
    from src.services.paper_service import PaperService
    
    mock_service = MagicMock(spec=PaperService)
    
    # デフォルトの検索結果
    async def mock_search_papers(query: str, max_results: int = 10):
        return [
            PaperMetadata(
                arxiv_id=f"2301.0000{i}",
                title=f"Paper {i}: {query}",
                authors=[f"Author {i}"],
                abstract=f"Abstract for paper {i} about {query}",
                year=2023,
                categories=["cs.AI"],
                pdf_url=f"https://arxiv.org/pdf/2301.0000{i}.pdf",
                published_date=datetime(2023, 1, i, 0, 0, 0)
            )
            for i in range(1, min(max_results + 1, 4))
        ]
    
    mock_service.search_papers = mock_search_papers
    
    return mock_service


@pytest.fixture
def sample_pdf_text() -> str:
    """サンプルPDFテキストフィクスチャ
    
    Returns:
        テスト用のPDFテキスト（IMRaD構造）
    """
    return """
Example Paper: A Novel Approach to Machine Learning

Abstract
This paper presents a novel approach to machine learning that improves accuracy by 15%.

Introduction
Machine learning has become increasingly important in recent years. However, existing approaches have limitations.
This paper addresses these limitations by proposing a new algorithm.

Methods
We propose a new algorithm that combines deep learning with reinforcement learning.
The algorithm consists of three main components: feature extraction, policy learning, and reward optimization.

Results
Our experiments show that the proposed algorithm achieves 15% higher accuracy than baseline methods.
We tested on three benchmark datasets: MNIST, CIFAR-10, and ImageNet.

Discussion
The results demonstrate the effectiveness of our approach. The improvement is particularly significant on complex datasets.
Future work will explore applications to other domains.

Conclusion
We presented a novel approach to machine learning that significantly improves accuracy.
The proposed algorithm is efficient and scalable.
"""


@pytest.fixture
def sample_chunks() -> List[Dict[str, Any]]:
    """サンプルチャンクフィクスチャ
    
    Returns:
        テスト用のチャンクリスト
    """
    return [
        {
            "text": "This paper presents a novel approach to machine learning that improves accuracy by 15%.",
            "section": "abstract",
            "chunk_id": 0
        },
        {
            "text": "Machine learning has become increasingly important in recent years. However, existing approaches have limitations.",
            "section": "introduction",
            "chunk_id": 0
        },
        {
            "text": "We propose a new algorithm that combines deep learning with reinforcement learning.",
            "section": "methods",
            "chunk_id": 0
        },
        {
            "text": "Our experiments show that the proposed algorithm achieves 15% higher accuracy than baseline methods.",
            "section": "results",
            "chunk_id": 0
        },
        {
            "text": "The results demonstrate the effectiveness of our approach.",
            "section": "discussion",
            "chunk_id": 0
        }
    ]


@pytest.fixture
def llm_config() -> LLMConfig:
    """LLM設定フィクスチャ
    
    Returns:
        テスト用のLLM設定
    """
    return LLMConfig(
        backend="gemini",
        gemini_model_name="gemini-1.5-flash",
        max_length=512,
        temperature=0.7
    )


@pytest.fixture
def embedding_config() -> EmbeddingConfig:
    """Embedding設定フィクスチャ
    
    Returns:
        テスト用のEmbedding設定
    """
    return EmbeddingConfig(
        backend="gemini",
        batch_size=32,
        normalize_embeddings=True
    )


@pytest.fixture
def chroma_config() -> ChromaConfig:
    """Chroma設定フィクスチャ
    
    Returns:
        テスト用のChroma設定
    """
    return ChromaConfig(
        persist_directory=":memory:",
        collection_name="test_collection"
    )
