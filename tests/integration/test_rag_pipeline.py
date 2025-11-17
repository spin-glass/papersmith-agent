"""RAGパイプライン統合テスト

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5

このテストは実際のChromaDBを使用し、LLM/Embeddingはモックを使用します。
インデックス化→検索→回答生成の完全なフローをテストします。
"""

import pytest
import pytest_asyncio
from pathlib import Path
import tempfile
import shutil
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.clients.arxiv_client import ArxivClient
from src.clients.chroma_client import ChromaClient
from src.services.paper_service import PaperService
from src.services.embedding_service import EmbeddingService
from src.services.llm_service import LLMService
from src.services.rag_service import RAGService, basic_rag_query
from src.models.config import ChromaConfig, EmbeddingConfig, LLMConfig


@pytest.fixture
def temp_dirs():
    """一時的なディレクトリを作成"""
    temp_base = Path(tempfile.mkdtemp())
    dirs = {
        "cache": temp_base / "cache",
        "chroma": temp_base / "chroma"
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    
    yield dirs
    
    # クリーンアップ
    if temp_base.exists():
        shutil.rmtree(temp_base)


@pytest.fixture
def arxiv_client(temp_dirs):
    """テスト用ArxivClientを作成"""
    return ArxivClient(
        cache_dir=temp_dirs["cache"] / "pdfs",
        max_retries=3,
        timeout=30
    )


@pytest.fixture
def paper_service(arxiv_client, temp_dirs):
    """テスト用PaperServiceを作成"""
    return PaperService(
        arxiv_client=arxiv_client,
        cache_dir=temp_dirs["cache"]
    )


@pytest.fixture
def chroma_client(temp_dirs):
    """テスト用ChromaClientを作成"""
    config = ChromaConfig(
        persist_dir=temp_dirs["chroma"],
        collection_name="test_rag_pipeline",
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
async def llm_service():
    """テスト用LLMServiceを作成（モデルロードはスキップ）"""
    config = LLMConfig(
        model_name="elyza/Llama-3-ELYZA-JP-8B",
        device="cpu",
        torch_dtype="float16"
    )
    service = LLMService(config)
    # 注意: 実際のLLMロードは重いのでテストではスキップ
    # await service.load_model()
    return service


@pytest_asyncio.fixture
async def rag_service(chroma_client, embedding_service):
    """テスト用RAGServiceを作成"""
    return RAGService(
        chroma_client=chroma_client,
        embedding_service=embedding_service
    )


@pytest.mark.asyncio
async def test_rag_pipeline_search_to_index(
    paper_service,
    rag_service
):
    """検索→ダウンロード→インデックス化"""
    # 1. 論文検索
    papers = await paper_service.search_papers(
        query="attention mechanism",
        max_results=1
    )
    assert len(papers) > 0
    
    paper = papers[0]
    arxiv_id = paper.arxiv_id
    
    # 2. PDF取得
    pdf_path = await paper_service.download_pdf(arxiv_id)
    assert pdf_path.exists()
    
    # 3. テキスト抽出
    text = await paper_service.extract_text(pdf_path)
    assert len(text) > 0
    
    # 4. メタデータ取得
    metadata = await paper_service.get_metadata(arxiv_id)
    
    # 5. インデックス化
    chunk_count = await rag_service.index_paper(
        arxiv_id=arxiv_id,
        text=text,
        metadata=metadata,
        chunk_size=512
    )
    
    # チャンクが作成されたことを確認
    assert chunk_count > 0
    
    # Chromaにドキュメントが追加されたことを確認
    assert rag_service.chroma.count() == chunk_count


@pytest.mark.asyncio
async def test_rag_pipeline_index_to_query(
    paper_service,
    rag_service
):
    """インデックス化→検索"""
    # 実在する論文を使用
    arxiv_id = "0704.0001"
    
    # 1. PDF取得
    pdf_path = await paper_service.download_pdf(arxiv_id)
    
    # 2. テキスト抽出
    text = await paper_service.extract_text(pdf_path)
    
    # 3. メタデータ取得
    metadata = await paper_service.get_metadata(arxiv_id)
    
    # 4. インデックス化
    chunk_count = await rag_service.index_paper(
        arxiv_id=arxiv_id,
        text=text,
        metadata=metadata
    )
    assert chunk_count > 0
    
    # 5. 検索を実行
    results = await rag_service.query(
        question="What is the main topic of this paper?",
        arxiv_ids=[arxiv_id],
        top_k=3
    )
    
    # 検索結果が返されることを確認
    assert len(results) > 0
    assert len(results) <= 3
    
    # 各結果が必要な属性を持つことを確認
    for result in results:
        assert result.chunk_id
        assert result.text
        assert result.score >= 0
        assert result.metadata["arxiv_id"] == arxiv_id


@pytest.mark.asyncio
async def test_rag_pipeline_multiple_papers(
    paper_service,
    rag_service
):
    """複数論文のインデックス化と検索"""
    # 2つの論文を使用
    arxiv_ids = ["0704.0001", "0704.0002"]
    
    # 各論文をインデックス化
    total_chunks = 0
    for arxiv_id in arxiv_ids:
        # PDF取得
        pdf_path = await paper_service.download_pdf(arxiv_id)
        
        # テキスト抽出
        text = await paper_service.extract_text(pdf_path)
        
        # メタデータ取得
        metadata = await paper_service.get_metadata(arxiv_id)
        
        # インデックス化
        chunk_count = await rag_service.index_paper(
            arxiv_id=arxiv_id,
            text=text,
            metadata=metadata
        )
        total_chunks += chunk_count
    
    # 全チャンクがインデックス化されたことを確認
    assert rag_service.chroma.count() == total_chunks
    
    # 全論文を対象に検索
    results_all = await rag_service.query(
        question="What is this paper about?",
        arxiv_ids=None,
        top_k=5
    )
    assert len(results_all) > 0
    
    # 特定の論文のみを対象に検索
    results_filtered = await rag_service.query(
        question="What is this paper about?",
        arxiv_ids=["0704.0001"],
        top_k=5
    )
    assert len(results_filtered) > 0
    assert all(r.metadata["arxiv_id"] == "0704.0001" for r in results_filtered)


@pytest.mark.asyncio
async def test_rag_pipeline_imrad_sections(
    paper_service,
    rag_service
):
    """IMRaD構造分割"""
    arxiv_id = "0704.0001"
    
    # PDF取得とテキスト抽出
    pdf_path = await paper_service.download_pdf(arxiv_id)
    text = await paper_service.extract_text(pdf_path)
    
    # IMRaD構造で分割
    sections = rag_service._split_by_imrad(text)
    
    # セクションが検出されることを確認
    assert len(sections) > 0
    
    # メタデータ取得
    metadata = await paper_service.get_metadata(arxiv_id)
    
    # インデックス化
    chunk_count = await rag_service.index_paper(
        arxiv_id=arxiv_id,
        text=text,
        metadata=metadata
    )
    
    # 検索してセクション情報が含まれることを確認
    results = await rag_service.query(
        question="introduction",
        arxiv_ids=[arxiv_id],
        top_k=3
    )
    
    # 各結果にセクション情報が含まれることを確認
    for result in results:
        assert "section" in result.metadata
        assert result.metadata["section"]


@pytest.mark.asyncio
async def test_rag_pipeline_context_building(
    paper_service,
    rag_service
):
    """コンテキスト構築"""
    from src.services.rag_service import build_context
    
    arxiv_id = "0704.0001"
    
    # インデックス化
    pdf_path = await paper_service.download_pdf(arxiv_id)
    text = await paper_service.extract_text(pdf_path)
    metadata = await paper_service.get_metadata(arxiv_id)
    
    await rag_service.index_paper(
        arxiv_id=arxiv_id,
        text=text,
        metadata=metadata
    )
    
    # 検索
    results = await rag_service.query(
        question="What is the main contribution?",
        arxiv_ids=[arxiv_id],
        top_k=3
    )
    
    # コンテキスト構築
    context = build_context(results)
    
    # コンテキストが構築されることを確認
    assert len(context) > 0
    assert isinstance(context, str)
    
    # コンテキストに論文情報が含まれることを確認
    assert arxiv_id in context or metadata.title in context


@pytest.mark.asyncio
async def test_rag_pipeline_empty_results(rag_service):
    """検索結果が空の場合"""
    from src.services.rag_service import build_context
    
    # インデックスが空の状態で検索
    results = await rag_service.query(
        question="This should return no results",
        arxiv_ids=["nonexistent_id"],
        top_k=5
    )
    
    # 結果が空であることを確認
    assert len(results) == 0
    
    # 空の結果からコンテキストを構築
    context = build_context(results)
    assert context == ""


@pytest.mark.asyncio
async def test_rag_pipeline_chunk_size_variation(
    paper_service,
    rag_service
):
    """異なるチャンクサイズでのインデックス化"""
    arxiv_id = "0704.0001"
    
    # PDF取得とテキスト抽出
    pdf_path = await paper_service.download_pdf(arxiv_id)
    text = await paper_service.extract_text(pdf_path)
    metadata = await paper_service.get_metadata(arxiv_id)
    
    # 小さいチャンクサイズでインデックス化
    chunk_count_small = await rag_service.index_paper(
        arxiv_id=arxiv_id,
        text=text,
        metadata=metadata,
        chunk_size=256
    )
    
    # チャンクが作成されることを確認
    assert chunk_count_small > 0
    
    # 検索が正常に動作することを確認
    results = await rag_service.query(
        question="What is this paper about?",
        arxiv_ids=[arxiv_id],
        top_k=3
    )
    assert len(results) > 0


@pytest.mark.asyncio
async def test_rag_pipeline_metadata_preservation(
    paper_service,
    rag_service
):
    """メタデータの保持"""
    arxiv_id = "0704.0001"
    
    # インデックス化
    pdf_path = await paper_service.download_pdf(arxiv_id)
    text = await paper_service.extract_text(pdf_path)
    metadata = await paper_service.get_metadata(arxiv_id)
    
    await rag_service.index_paper(
        arxiv_id=arxiv_id,
        text=text,
        metadata=metadata
    )
    
    # 検索
    results = await rag_service.query(
        question="test query",
        arxiv_ids=[arxiv_id],
        top_k=3
    )
    
    # 各結果が必要なメタデータを持つことを確認
    for result in results:
        assert result.metadata["arxiv_id"] == arxiv_id
        assert result.metadata["title"] == metadata.title
        assert result.metadata["year"] == metadata.year
        assert "section" in result.metadata
        assert "chunk_id" in result.metadata
        
        # chunk_idの形式を確認
        assert result.metadata["chunk_id"].startswith(arxiv_id)


@pytest.mark.asyncio
async def test_rag_pipeline_full_flow_with_answer_generation(
    paper_service,
    rag_service,
    mock_llm_service
):
    """完全なRAGフロー: インデックス化→検索→回答生成
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
    """
    arxiv_id = "0704.0001"
    
    # 1. 論文のインデックス化
    pdf_path = await paper_service.download_pdf(arxiv_id)
    text = await paper_service.extract_text(pdf_path)
    metadata = await paper_service.get_metadata(arxiv_id)
    
    chunk_count = await rag_service.index_paper(
        arxiv_id=arxiv_id,
        text=text,
        metadata=metadata
    )
    assert chunk_count > 0
    
    # 2. 検索実行
    question = "What is the main contribution of this paper?"
    results = await rag_service.query(
        question=question,
        arxiv_ids=[arxiv_id],
        top_k=3
    )
    assert len(results) > 0
    
    # 3. 回答生成（モックLLMを使用）
    from src.services.rag_service import build_context
    context = build_context(results)
    
    answer = await mock_llm_service.generate(
        question=question,
        context=context
    )
    
    # 回答が生成されることを確認
    assert len(answer) > 0
    assert isinstance(answer, str)
    assert question in answer or "テスト回答" in answer


@pytest.mark.asyncio
async def test_rag_pipeline_basic_rag_query(
    paper_service,
    rag_service,
    embedding_service,
    mock_llm_service
):
    """basic_rag_query関数のテスト
    
    Requirements: 2.4, 2.5
    """
    arxiv_id = "0704.0001"
    
    # インデックス化
    pdf_path = await paper_service.download_pdf(arxiv_id)
    text = await paper_service.extract_text(pdf_path)
    metadata = await paper_service.get_metadata(arxiv_id)
    
    await rag_service.index_paper(
        arxiv_id=arxiv_id,
        text=text,
        metadata=metadata
    )
    
    # basic_rag_queryを実行
    question = "What is this paper about?"
    response = await basic_rag_query(
        question=question,
        arxiv_ids=[arxiv_id],
        chroma_client=rag_service.chroma,
        embedding_service=embedding_service,
        llm_service=mock_llm_service,
        top_k=3
    )
    
    # レスポンスの検証
    assert response.answer
    assert len(response.answer) > 0
    assert len(response.sources) > 0
    assert len(response.sources) <= 3
    
    # ソースの検証
    for source in response.sources:
        assert source.chunk_id
        assert source.text
        assert source.score >= 0
        assert source.metadata["arxiv_id"] == arxiv_id


@pytest.mark.asyncio
async def test_rag_pipeline_persistence(
    temp_dirs,
    paper_service,
    embedding_service
):
    """Chromaの永続化テスト
    
    Requirements: 2.2, 2.3
    """
    arxiv_id = "0704.0001"
    
    # 最初のChromaクライアントでインデックス化
    config1 = ChromaConfig(
        persist_dir=temp_dirs["chroma"],
        collection_name="test_persistence",
        distance_metric="cosine"
    )
    client1 = ChromaClient(config1)
    client1.initialize()
    
    rag_service1 = RAGService(
        chroma_client=client1,
        embedding_service=embedding_service
    )
    
    # インデックス化
    pdf_path = await paper_service.download_pdf(arxiv_id)
    text = await paper_service.extract_text(pdf_path)
    metadata = await paper_service.get_metadata(arxiv_id)
    
    chunk_count = await rag_service1.index_paper(
        arxiv_id=arxiv_id,
        text=text,
        metadata=metadata
    )
    assert chunk_count > 0
    
    # 2つ目のChromaクライアントで同じディレクトリから読み込み
    config2 = ChromaConfig(
        persist_dir=temp_dirs["chroma"],
        collection_name="test_persistence",
        distance_metric="cosine"
    )
    client2 = ChromaClient(config2)
    client2.initialize()
    
    # データが永続化されていることを確認
    assert client2.count() == chunk_count
    
    # 検索が正常に動作することを確認
    rag_service2 = RAGService(
        chroma_client=client2,
        embedding_service=embedding_service
    )
    
    results = await rag_service2.query(
        question="test query",
        arxiv_ids=[arxiv_id],
        top_k=3
    )
    assert len(results) > 0


@pytest.mark.asyncio
async def test_rag_pipeline_error_handling(
    rag_service,
    embedding_service,
    mock_llm_service
):
    """エラーハンドリングのテスト
    
    Requirements: 2.4, 2.5
    """
    # 空のインデックスで検索
    results = await rag_service.query(
        question="This should return empty results",
        arxiv_ids=["nonexistent"],
        top_k=5
    )
    assert len(results) == 0
    
    # 空の結果でbasic_rag_queryを実行
    response = await basic_rag_query(
        question="This should handle empty results",
        arxiv_ids=["nonexistent"],
        chroma_client=rag_service.chroma,
        embedding_service=embedding_service,
        llm_service=mock_llm_service,
        top_k=5
    )
    
    # 空の結果でも回答が生成されることを確認
    assert response.answer
    assert len(response.sources) == 0
