"""RAGServiceのユニットテスト

Requirements: 2.1, 2.2, 2.3, 2.4
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from src.clients.chroma_client import ChromaClient
from src.models.paper import PaperMetadata
from src.models.rag import RAGResponse, SearchResult
from src.services.embedding_service import EmbeddingService
from src.services.llm_service import LLMService
from src.services.rag_service import RAGService, basic_rag_query, build_context


@pytest.fixture
def mock_chroma_client():
    """モックChromaClient"""
    client = Mock(spec=ChromaClient)
    client.add = Mock()
    client.search = Mock(return_value=[])
    return client


@pytest.fixture
def mock_embedding_service():
    """モックEmbeddingService"""
    service = Mock(spec=EmbeddingService)
    service.embed = AsyncMock(return_value=[0.1] * 768)
    service.embed_batch = AsyncMock(return_value=[[0.1] * 768, [0.2] * 768])
    return service


@pytest.fixture
def mock_llm_service():
    """モックLLMService"""
    service = Mock(spec=LLMService)
    service.generate = AsyncMock(return_value="これはテスト回答です。")
    return service


@pytest.fixture
def rag_service(mock_chroma_client, mock_embedding_service):
    """RAGServiceインスタンス"""
    return RAGService(
        chroma_client=mock_chroma_client,
        embedding_service=mock_embedding_service
    )


@pytest.fixture
def sample_paper_metadata():
    """サンプル論文メタデータ"""
    return PaperMetadata(
        arxiv_id="2301.00001",
        title="Test Paper",
        authors=["Author One"],
        abstract="Test abstract",
        year=2023,
        categories=["cs.AI"],
        pdf_url="https://example.com/test.pdf",
        published_date=datetime(2023, 1, 1)
    )


# ========================================
# IMRaD分割テスト (Requirement 2.1)
# ========================================

def test_split_by_imrad_with_all_sections(rag_service):
    """IMRaD構造で全セクションを検出"""
    text = """
Abstract
This is the abstract.

1. Introduction
This is the introduction.

2. Methods
This is the methods section.

3. Results
This is the results section.

4. Discussion
This is the discussion.

5. Conclusion
This is the conclusion.

References
[1] Reference one
"""

    sections = rag_service._split_by_imrad(text)

    # 主要セクションが検出されることを確認
    assert len(sections) > 0
    assert "abstract" in sections
    assert "introduction" in sections
    assert "methods" in sections
    assert "results" in sections
    assert "discussion" in sections
    assert "conclusion" in sections

    # 各セクションにテキストが含まれることを確認
    assert "abstract" in sections["abstract"].lower()
    assert "introduction" in sections["introduction"].lower()


def test_split_by_imrad_with_partial_sections(rag_service):
    """一部のセクションのみ存在する場合"""
    text = """
Abstract
This is the abstract.

Introduction
This is the introduction.

Conclusion
This is the conclusion.
"""

    sections = rag_service._split_by_imrad(text)

    # 検出されたセクションのみが含まれることを確認
    assert "abstract" in sections
    assert "introduction" in sections
    assert "conclusion" in sections
    # 存在しないセクションは含まれない
    assert "methods" not in sections
    assert "results" not in sections


def test_split_by_imrad_no_sections(rag_service):
    """セクションが検出されない場合は全体をfull_textとして扱う"""
    text = "This is just plain text without any section headers."

    sections = rag_service._split_by_imrad(text)

    # full_textとして扱われることを確認
    assert "full_text" in sections
    assert sections["full_text"] == text


def test_split_by_imrad_japanese_sections(rag_service):
    """日本語のセクション見出しを検出"""
    text = """
要旨
これは要旨です。

1. はじめに
これは序論です。

2. 手法
これは手法です。

3. 結果
これは結果です。

4. 考察
これは考察です。

5. まとめ
これはまとめです。
"""

    sections = rag_service._split_by_imrad(text)

    # 日本語セクションが検出されることを確認
    assert len(sections) > 0
    # abstract, introduction, methods, results, discussion, conclusionのいずれかが検出される
    assert any(key in ["abstract", "introduction", "methods", "results", "discussion", "conclusion"]
               for key in sections.keys())


def test_split_by_imrad_case_insensitive(rag_service):
    """大文字小文字を区別せずに検出"""
    text = """
ABSTRACT
This is the abstract.

INTRODUCTION
This is the introduction.
"""

    sections = rag_service._split_by_imrad(text)

    # 大文字でも検出されることを確認
    assert "abstract" in sections
    assert "introduction" in sections


# ========================================
# チャンク化テスト (Requirement 2.1)
# ========================================

def test_chunk_text_basic(rag_service):
    """基本的なテキストチャンク化"""
    text = "This is sentence one. This is sentence two. This is sentence three."

    chunks = rag_service._chunk_text(text, chunk_size=30)

    # チャンクが作成されることを確認
    assert len(chunks) > 0
    # 各チャンクがchunk_size以下であることを確認（多少の余裕を持たせる）
    for chunk in chunks:
        assert len(chunk) <= 50


def test_chunk_text_respects_sentence_boundaries(rag_service):
    """文の途中で切らないことを確認"""
    text = "First sentence. Second sentence. Third sentence."

    chunks = rag_service._chunk_text(text, chunk_size=20)

    # 各チャンクが完全な文で構成されることを確認
    for chunk in chunks:
        # 文末記号で終わるか、最後のチャンクであることを確認
        assert chunk.strip().endswith('.') or chunk == chunks[-1]


def test_chunk_text_empty_input(rag_service):
    """空のテキストの場合は空リストを返す"""
    text = ""

    chunks = rag_service._chunk_text(text, chunk_size=100)

    assert chunks == []


def test_chunk_text_whitespace_only(rag_service):
    """空白のみのテキストの場合は空リストを返す"""
    text = "   \n\n   "

    chunks = rag_service._chunk_text(text, chunk_size=100)

    assert chunks == []


def test_chunk_text_long_sentence(rag_service):
    """chunk_sizeを超える長い文は強制的に分割"""
    # 100文字を超える長い文
    long_sentence = "A" * 150 + "."

    chunks = rag_service._chunk_text(long_sentence, chunk_size=100)

    # 複数のチャンクに分割されることを確認
    assert len(chunks) > 1
    # 各チャンクがchunk_size以下であることを確認
    for chunk in chunks:
        assert len(chunk) <= 100


def test_chunk_text_japanese(rag_service):
    """日本語テキストのチャンク化"""
    text = "これは最初の文です。これは二番目の文です。これは三番目の文です。"

    chunks = rag_service._chunk_text(text, chunk_size=50)

    # チャンクが作成されることを確認
    assert len(chunks) > 0
    # 各チャンクに日本語テキストが含まれることを確認
    for chunk in chunks:
        assert len(chunk) > 0
        assert 'です' in chunk or 'ます' in chunk or '。' in chunk


def test_chunk_text_mixed_delimiters(rag_service):
    """複数の文末記号が混在する場合"""
    text = "First sentence. Second sentence! Third sentence? Fourth sentence."

    chunks = rag_service._chunk_text(text, chunk_size=50)

    # チャンクが作成されることを確認
    assert len(chunks) > 0


# ========================================
# インデックス化テスト (Requirements 2.1, 2.2, 2.3)
# ========================================

@pytest.mark.asyncio
async def test_index_paper_basic(rag_service, sample_paper_metadata, mock_chroma_client, mock_embedding_service):
    """基本的な論文インデックス化"""
    text = """
Abstract
This is a test paper.

Introduction
This paper discusses testing.
"""

    # 実行
    chunk_count = await rag_service.index_paper(
        arxiv_id="2301.00001",
        text=text,
        metadata=sample_paper_metadata,
        chunk_size=100
    )

    # 検証
    assert chunk_count > 0
    assert mock_embedding_service.embed_batch.called
    assert mock_chroma_client.add.called


@pytest.mark.asyncio
async def test_index_paper_metadata_included(rag_service, sample_paper_metadata, mock_chroma_client, mock_embedding_service):
    """インデックス化時にメタデータが含まれることを確認 (Requirement 2.3)"""
    text = """
Abstract
This is a test paper about machine learning.
"""

    # 実行
    await rag_service.index_paper(
        arxiv_id="2301.00001",
        text=text,
        metadata=sample_paper_metadata,
        chunk_size=100
    )

    # Chromaに追加された際のメタデータを確認
    assert mock_chroma_client.add.called

    # 最初の呼び出しの引数を取得
    call_args = mock_chroma_client.add.call_args
    metadata = call_args[1]["metadata"]

    # 必須メタデータが含まれることを確認
    assert "arxiv_id" in metadata
    assert "title" in metadata
    assert "authors" in metadata
    assert "year" in metadata
    assert "section" in metadata
    assert "chunk_id" in metadata

    # 値が正しいことを確認
    assert metadata["arxiv_id"] == "2301.00001"
    assert metadata["title"] == sample_paper_metadata.title
    assert metadata["year"] == sample_paper_metadata.year


@pytest.mark.asyncio
async def test_index_paper_multiple_sections(rag_service, sample_paper_metadata, mock_chroma_client, mock_embedding_service):
    """複数セクションを持つ論文のインデックス化"""
    text = """
Abstract
This is the abstract.

Introduction
This is the introduction with multiple sentences. It discusses the background.

Methods
This is the methods section. It describes the approach.

Results
This is the results section. It presents the findings.
"""

    # 実行
    chunk_count = await rag_service.index_paper(
        arxiv_id="2301.00001",
        text=text,
        metadata=sample_paper_metadata,
        chunk_size=50
    )

    # 複数のチャンクが作成されることを確認
    assert chunk_count > 1

    # 複数回Chromaに追加されることを確認
    assert mock_chroma_client.add.call_count > 1


@pytest.mark.asyncio
async def test_index_paper_empty_text(rag_service, sample_paper_metadata, mock_chroma_client, mock_embedding_service):
    """空のテキストの場合"""
    text = ""

    # 実行
    chunk_count = await rag_service.index_paper(
        arxiv_id="2301.00001",
        text=text,
        metadata=sample_paper_metadata,
        chunk_size=100
    )

    # チャンクが作成されないことを確認
    assert chunk_count == 0
    assert not mock_chroma_client.add.called


@pytest.mark.asyncio
async def test_index_paper_chunk_id_format(rag_service, sample_paper_metadata, mock_chroma_client, mock_embedding_service):
    """chunk_idのフォーマットが正しいことを確認"""
    text = """
Abstract
This is a test paper.
"""

    # 実行
    await rag_service.index_paper(
        arxiv_id="2301.00001",
        text=text,
        metadata=sample_paper_metadata,
        chunk_size=100
    )

    # chunk_idのフォーマットを確認
    call_args = mock_chroma_client.add.call_args
    chunk_id = call_args[1]["chunk_id"]

    # フォーマット: {arxiv_id}_{section}_{index}
    assert chunk_id.startswith("2301.00001_")
    assert "_abstract_" in chunk_id or "_full_text_" in chunk_id


@pytest.mark.asyncio
async def test_index_paper_batch_embedding(rag_service, sample_paper_metadata, mock_chroma_client, mock_embedding_service):
    """バッチでEmbeddingが生成されることを確認 (Requirement 2.2)"""
    text = """
Abstract
This is the abstract.

Introduction
This is the introduction.

Methods
This is the methods.
"""

    # 実行
    await rag_service.index_paper(
        arxiv_id="2301.00001",
        text=text,
        metadata=sample_paper_metadata,
        chunk_size=50
    )

    # embed_batchが呼ばれることを確認（embedは呼ばれない）
    assert mock_embedding_service.embed_batch.called

    # バッチサイズが適切であることを確認
    call_args = mock_embedding_service.embed_batch.call_args
    texts = call_args[0][0]
    assert len(texts) > 0


# ========================================
# 検索テスト (Requirement 2.4)
# ========================================

@pytest.mark.asyncio
async def test_query_basic(rag_service, mock_chroma_client, mock_embedding_service):
    """基本的なベクター検索"""
    # モックの設定
    mock_search_result = SearchResult(
        chunk_id="test_chunk_1",
        text="This is a test result.",
        score=0.9,
        metadata={"arxiv_id": "2301.00001", "section": "introduction"}
    )
    mock_chroma_client.search.return_value = [mock_search_result]

    # 実行
    results = await rag_service.query(
        question="What is this paper about?",
        arxiv_ids=["2301.00001"],
        top_k=5
    )

    # 検証
    assert len(results) == 1
    assert results[0].chunk_id == "test_chunk_1"
    assert mock_embedding_service.embed.called
    assert mock_chroma_client.search.called


@pytest.mark.asyncio
async def test_query_with_arxiv_ids_filter(rag_service, mock_chroma_client, mock_embedding_service):
    """arxiv_idsフィルタリング付き検索"""
    mock_chroma_client.search.return_value = []

    # 実行
    arxiv_ids = ["2301.00001", "2301.00002"]
    await rag_service.query(
        question="Test question",
        arxiv_ids=arxiv_ids,
        top_k=5
    )

    # Chromaの検索にarxiv_idsが渡されることを確認
    call_args = mock_chroma_client.search.call_args
    assert call_args[1]["arxiv_ids"] == arxiv_ids


@pytest.mark.asyncio
async def test_query_without_arxiv_ids_filter(rag_service, mock_chroma_client, mock_embedding_service):
    """arxiv_idsフィルタなし（全論文対象）"""
    mock_chroma_client.search.return_value = []

    # 実行
    await rag_service.query(
        question="Test question",
        arxiv_ids=None,
        top_k=5
    )

    # Chromaの検索にNoneが渡されることを確認
    call_args = mock_chroma_client.search.call_args
    assert call_args[1]["arxiv_ids"] is None


@pytest.mark.asyncio
async def test_query_top_k_parameter(rag_service, mock_chroma_client, mock_embedding_service):
    """top_kパラメータが正しく渡されることを確認"""
    mock_chroma_client.search.return_value = []

    # 実行
    await rag_service.query(
        question="Test question",
        top_k=10
    )

    # Chromaの検索にtop_kが渡されることを確認
    call_args = mock_chroma_client.search.call_args
    assert call_args[1]["top_k"] == 10


@pytest.mark.asyncio
async def test_query_embedding_generation(rag_service, mock_chroma_client, mock_embedding_service):
    """質問がEmbedding化されることを確認"""
    mock_chroma_client.search.return_value = []

    question = "What is machine learning?"

    # 実行
    await rag_service.query(question=question)

    # embedが呼ばれることを確認
    mock_embedding_service.embed.assert_called_once_with(question)

    # 生成されたEmbeddingがChromaに渡されることを確認
    call_args = mock_chroma_client.search.call_args
    assert call_args[1]["query_embedding"] == [0.1] * 768


@pytest.mark.asyncio
async def test_query_returns_search_results(rag_service, mock_chroma_client, mock_embedding_service):
    """検索結果が正しく返されることを確認"""
    # 複数の検索結果を設定
    mock_results = [
        SearchResult(
            chunk_id=f"chunk_{i}",
            text=f"Result {i}",
            score=0.9 - i * 0.1,
            metadata={"arxiv_id": "2301.00001", "section": "introduction"}
        )
        for i in range(3)
    ]
    mock_chroma_client.search.return_value = mock_results

    # 実行
    results = await rag_service.query(question="Test")

    # 結果が正しく返されることを確認
    assert len(results) == 3
    assert results[0].chunk_id == "chunk_0"
    assert results[1].chunk_id == "chunk_1"
    assert results[2].chunk_id == "chunk_2"


# ========================================
# コンテキスト構築テスト (Requirement 2.4)
# ========================================

def test_build_context_basic():
    """基本的なコンテキスト構築"""
    results = [
        SearchResult(
            chunk_id="chunk_1",
            text="This is the first result.",
            score=0.9,
            metadata={
                "arxiv_id": "2301.00001",
                "title": "Test Paper",
                "section": "introduction"
            }
        ),
        SearchResult(
            chunk_id="chunk_2",
            text="This is the second result.",
            score=0.8,
            metadata={
                "arxiv_id": "2301.00002",
                "title": "Another Paper",
                "section": "methods"
            }
        )
    ]

    context = build_context(results)

    # 必要な情報が含まれることを確認
    assert "Test Paper" in context
    assert "Another Paper" in context
    assert "This is the first result." in context
    assert "This is the second result." in context
    assert "2301.00001" in context
    assert "2301.00002" in context
    assert "introduction" in context
    assert "methods" in context


def test_build_context_empty_results():
    """空の検索結果の場合"""
    results = []

    context = build_context(results)

    # 空文字列が返されることを確認
    assert context == ""


def test_build_context_numbering():
    """文献番号が正しく付与されることを確認"""
    results = [
        SearchResult(
            chunk_id=f"chunk_{i}",
            text=f"Result {i}",
            score=0.9,
            metadata={
                "arxiv_id": f"2301.0000{i}",
                "title": f"Paper {i}",
                "section": "introduction"
            }
        )
        for i in range(1, 4)
    ]

    context = build_context(results)

    # 文献番号が含まれることを確認
    assert "[文献 1]" in context
    assert "[文献 2]" in context
    assert "[文献 3]" in context


def test_build_context_missing_metadata():
    """メタデータが欠けている場合のデフォルト値"""
    results = [
        SearchResult(
            chunk_id="chunk_1",
            text="Test result",
            score=0.9,
            metadata={}  # メタデータが空
        )
    ]

    context = build_context(results)

    # デフォルト値が使用されることを確認
    assert "Unknown" in context
    assert "unknown" in context


def test_build_context_format():
    """コンテキストのフォーマットが正しいことを確認"""
    results = [
        SearchResult(
            chunk_id="chunk_1",
            text="Test content",
            score=0.9,
            metadata={
                "arxiv_id": "2301.00001",
                "title": "Test Paper",
                "section": "introduction"
            }
        )
    ]

    context = build_context(results)

    # 期待されるフォーマット要素が含まれることを確認
    assert "[文献 1]" in context
    assert "Test Paper" in context
    assert "arXiv: 2301.00001" in context
    assert "セクション: introduction" in context
    assert "Test content" in context


# ========================================
# basic_rag_query テスト (Requirements 2.4, 2.5)
# ========================================

@pytest.mark.asyncio
async def test_basic_rag_query_success(mock_chroma_client, mock_embedding_service, mock_llm_service):
    """basic_rag_queryの正常系"""
    # モックの設定
    mock_results = [
        SearchResult(
            chunk_id="chunk_1",
            text="Test result",
            score=0.9,
            metadata={
                "arxiv_id": "2301.00001",
                "title": "Test Paper",
                "section": "introduction"
            }
        )
    ]
    mock_chroma_client.search.return_value = mock_results

    # 実行
    response = await basic_rag_query(
        question="What is this about?",
        arxiv_ids=["2301.00001"],
        chroma_client=mock_chroma_client,
        embedding_service=mock_embedding_service,
        llm_service=mock_llm_service,
        top_k=5
    )

    # 検証
    assert isinstance(response, RAGResponse)
    assert response.answer == "これはテスト回答です。"
    assert len(response.sources) == 1
    assert response.metadata["results_found"] == 1
    assert "context_length" in response.metadata


@pytest.mark.asyncio
async def test_basic_rag_query_no_results(mock_chroma_client, mock_embedding_service, mock_llm_service):
    """検索結果が見つからない場合"""
    # モックの設定
    mock_chroma_client.search.return_value = []

    # 実行
    response = await basic_rag_query(
        question="What is this about?",
        arxiv_ids=None,
        chroma_client=mock_chroma_client,
        embedding_service=mock_embedding_service,
        llm_service=mock_llm_service,
        top_k=5
    )

    # 検証
    assert isinstance(response, RAGResponse)
    assert "関連する情報が見つかりませんでした" in response.answer
    assert len(response.sources) == 0
    assert response.metadata["results_found"] == 0


@pytest.mark.asyncio
async def test_basic_rag_query_context_building(mock_chroma_client, mock_embedding_service, mock_llm_service):
    """コンテキストが正しく構築されてLLMに渡されることを確認"""
    # モックの設定
    mock_results = [
        SearchResult(
            chunk_id="chunk_1",
            text="First result",
            score=0.9,
            metadata={
                "arxiv_id": "2301.00001",
                "title": "Paper 1",
                "section": "introduction"
            }
        ),
        SearchResult(
            chunk_id="chunk_2",
            text="Second result",
            score=0.8,
            metadata={
                "arxiv_id": "2301.00002",
                "title": "Paper 2",
                "section": "methods"
            }
        )
    ]
    mock_chroma_client.search.return_value = mock_results

    # 実行
    await basic_rag_query(
        question="Test question",
        arxiv_ids=None,
        chroma_client=mock_chroma_client,
        embedding_service=mock_embedding_service,
        llm_service=mock_llm_service,
        top_k=5
    )

    # LLMのgenerateが呼ばれることを確認
    assert mock_llm_service.generate.called

    # コンテキストに両方の結果が含まれることを確認
    call_args = mock_llm_service.generate.call_args
    context = call_args[0][1]
    assert "First result" in context
    assert "Second result" in context
    assert "Paper 1" in context
    assert "Paper 2" in context


@pytest.mark.asyncio
async def test_basic_rag_query_metadata(mock_chroma_client, mock_embedding_service, mock_llm_service):
    """レスポンスのメタデータが正しいことを確認"""
    # モックの設定
    mock_results = [
        SearchResult(
            chunk_id=f"chunk_{i}",
            text=f"Result {i}",
            score=0.9,
            metadata={"arxiv_id": "2301.00001", "title": "Test", "section": "intro"}
        )
        for i in range(3)
    ]
    mock_chroma_client.search.return_value = mock_results

    # 実行
    response = await basic_rag_query(
        question="Test",
        arxiv_ids=None,
        chroma_client=mock_chroma_client,
        embedding_service=mock_embedding_service,
        llm_service=mock_llm_service,
        top_k=5
    )

    # メタデータを確認
    assert response.metadata["results_found"] == 3
    assert response.metadata["context_length"] > 0


# ========================================
# エラーハンドリングテスト
# ========================================

@pytest.mark.asyncio
async def test_index_paper_error_handling(mock_chroma_client, mock_embedding_service):
    """インデックス化時のエラーハンドリング"""
    # Embeddingサービスがエラーを投げるように設定
    mock_embedding_service.embed_batch = AsyncMock(side_effect=Exception("Embedding error"))

    rag_service = RAGService(
        chroma_client=mock_chroma_client,
        embedding_service=mock_embedding_service
    )

    metadata = PaperMetadata(
        arxiv_id="2301.00001",
        title="Test",
        authors=["Test"],
        abstract="Test",
        year=2023,
        categories=["cs.AI"],
        pdf_url="https://test.com",
        published_date=datetime(2023, 1, 1)
    )

    # エラーが再スローされることを確認
    with pytest.raises(Exception, match="Embedding error"):
        await rag_service.index_paper(
            arxiv_id="2301.00001",
            text="Test text",
            metadata=metadata
        )


@pytest.mark.asyncio
async def test_query_error_handling(mock_chroma_client, mock_embedding_service):
    """検索時のエラーハンドリング"""
    # Embeddingサービスがエラーを投げるように設定
    mock_embedding_service.embed = AsyncMock(side_effect=Exception("Embedding error"))

    rag_service = RAGService(
        chroma_client=mock_chroma_client,
        embedding_service=mock_embedding_service
    )

    # エラーが再スローされることを確認
    with pytest.raises(Exception, match="Embedding error"):
        await rag_service.query(question="Test question")


@pytest.mark.asyncio
async def test_basic_rag_query_error_handling(mock_chroma_client, mock_embedding_service, mock_llm_service):
    """basic_rag_query時のエラーハンドリング"""
    # LLMサービスがエラーを投げるように設定
    mock_llm_service.generate = AsyncMock(side_effect=Exception("LLM error"))

    # 検索結果を設定
    mock_results = [
        SearchResult(
            chunk_id="chunk_1",
            text="Test",
            score=0.9,
            metadata={"arxiv_id": "2301.00001", "title": "Test", "section": "intro"}
        )
    ]
    mock_chroma_client.search.return_value = mock_results

    # エラーが再スローされることを確認
    with pytest.raises(Exception, match="LLM error"):
        await basic_rag_query(
            question="Test",
            arxiv_ids=None,
            chroma_client=mock_chroma_client,
            embedding_service=mock_embedding_service,
            llm_service=mock_llm_service
        )


def test_chunk_text_with_empty_sentences(rag_service):
    """空の文が含まれる場合のチャンク化"""
    # 複数の空白や改行が含まれるテキスト
    text = "First sentence.  \n\n  Second sentence.   \n   Third sentence."

    chunks = rag_service._chunk_text(text, chunk_size=50)

    # チャンクが作成されることを確認
    assert len(chunks) > 0
    # 空のチャンクが含まれないことを確認
    for chunk in chunks:
        assert chunk.strip() != ""
