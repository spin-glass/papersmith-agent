"""RAG処理サービス

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

import logging
import re
from typing import Optional

from src.clients.chroma_client import ChromaClient
from src.models.paper import PaperMetadata
from src.models.rag import RAGResponse, SearchResult
from src.services.embedding_service import EmbeddingService
from src.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class RAGService:
    """RAG処理サービス

    論文のインデックス化、ベクター検索、RAGクエリ処理を提供します。

    Requirements:
    - 2.1: IMRaD構造に基づいてセクション単位でテキストをチャンク化
    - 2.2: 各チャンクに対してembeddingを生成しChromaベクターストアに保存
    - 2.3: メタデータ（arxiv_id、title、authors、year、section、chunk_id）を含める
    - 2.4: Chromaベクターストアから関連チャンクを検索
    - 2.5: LLMを使用して検索結果に基づく回答を生成
    """

    def __init__(
        self,
        chroma_client: ChromaClient,
        embedding_service: EmbeddingService,
        llm_service: Optional[LLMService] = None
    ):
        """初期化

        Args:
            chroma_client: Chromaクライアント
            embedding_service: Embeddingサービス
            llm_service: LLMサービス（basic_rag_query使用時に必要）
        """
        self.chroma = chroma_client
        self.embedding = embedding_service
        self.llm = llm_service

        logger.info("RAGService initialized")

    async def index_paper(
        self,
        arxiv_id: str,
        text: str,
        metadata: PaperMetadata,
        chunk_size: int = 512
    ) -> int:
        """論文をインデックス化

        テキストをIMRaD構造で分割し、チャンク化してChromaに保存します。

        Args:
            arxiv_id: 論文ID
            text: 論文の全文テキスト
            metadata: 論文メタデータ
            chunk_size: チャンクサイズ（文字数）

        Returns:
            インデックス化されたチャンク数

        Requirements: 2.1, 2.2, 2.3
        """
        try:
            logger.info(f"Indexing paper: arxiv_id={arxiv_id}")

            # IMRaD構造でセクション分割
            sections = self._split_by_imrad(text)
            logger.debug(f"Split into {len(sections)} sections")

            # チャンク化
            chunks = []
            for section_name, section_text in sections.items():
                if not section_text.strip():
                    continue

                section_chunks = self._chunk_text(section_text, chunk_size=chunk_size)

                for i, chunk in enumerate(section_chunks):
                    chunk_id = f"{arxiv_id}_{section_name}_{i}"
                    chunks.append({
                        "chunk_id": chunk_id,
                        "text": chunk,
                        "metadata": {
                            "arxiv_id": arxiv_id,
                            "title": metadata.title,
                            "authors": metadata.authors,
                            "year": metadata.year,
                            "section": section_name,
                            "chunk_id": chunk_id
                        }
                    })

            logger.info(f"Created {len(chunks)} chunks from {len(sections)} sections")

            # Embedding生成とChromaに保存
            if chunks:
                # バッチでEmbedding生成
                texts = [chunk["text"] for chunk in chunks]
                embeddings = await self.embedding.embed_batch(texts)

                # Chromaに追加
                for chunk, embedding in zip(chunks, embeddings, strict=False):
                    self.chroma.add(
                        embedding=embedding,
                        text=chunk["text"],
                        metadata=chunk["metadata"],
                        chunk_id=chunk["chunk_id"]
                    )

                logger.info(
                    f"Successfully indexed paper: arxiv_id={arxiv_id}, "
                    f"chunks={len(chunks)}"
                )
            else:
                logger.warning(f"No chunks created for paper: arxiv_id={arxiv_id}")

            return len(chunks)

        except Exception as e:
            logger.error(f"Failed to index paper {arxiv_id}: {e}")
            raise

    async def query(
        self,
        question: str,
        arxiv_ids: Optional[list[str]] = None,
        top_k: int = 5
    ) -> list[SearchResult]:
        """ベクター検索を実行

        質問をEmbedding化してChromaベクターストアから関連チャンクを検索します。

        Args:
            question: 検索クエリ（質問）
            arxiv_ids: フィルタリングする論文IDリスト（Noneの場合は全論文を対象）
            top_k: 取得する結果数

        Returns:
            検索結果のリスト

        Requirements: 2.4
        """
        try:
            logger.info(
                f"Querying: question='{question[:50]}...', "
                f"arxiv_ids={arxiv_ids}, top_k={top_k}"
            )

            # 質問をEmbedding化
            query_embedding = await self.embedding.embed(question)

            # Chromaベクター検索
            results = self.chroma.search(
                query_embedding=query_embedding,
                arxiv_ids=arxiv_ids,
                top_k=top_k
            )

            logger.info(f"Query completed: found {len(results)} results")

            return results

        except Exception as e:
            logger.error(f"Failed to query: {e}")
            raise

    def _split_by_imrad(self, text: str) -> dict[str, str]:
        """IMRaD構造でセクション分割

        ヒューリスティックなセクション検出を行います。
        論文の一般的なセクション見出しパターンを使用して分割します。

        Args:
            text: 論文の全文テキスト

        Returns:
            セクション名をキー、セクションテキストを値とする辞書

        Requirements: 2.1
        """
        # セクション定義（優先順位順）
        section_patterns = {
            "abstract": [
                r"\n\s*abstract\s*\n",
                r"\n\s*要旨\s*\n",
                r"\n\s*概要\s*\n"
            ],
            "introduction": [
                r"\n\s*(?:1\.?\s+)?introduction\s*\n",
                r"\n\s*(?:1\.?\s+)?はじめに\s*\n",
                r"\n\s*(?:1\.?\s+)?序論\s*\n"
            ],
            "methods": [
                r"\n\s*(?:\d+\.?\s+)?(?:methods?|methodology|approach|proposed method)\s*\n",
                r"\n\s*(?:\d+\.?\s+)?(?:手法|提案手法|方法論)\s*\n"
            ],
            "results": [
                r"\n\s*(?:\d+\.?\s+)?(?:results?|experiments?|evaluation)\s*\n",
                r"\n\s*(?:\d+\.?\s+)?(?:結果|実験|評価)\s*\n"
            ],
            "discussion": [
                r"\n\s*(?:\d+\.?\s+)?discussion\s*\n",
                r"\n\s*(?:\d+\.?\s+)?(?:考察|議論)\s*\n"
            ],
            "conclusion": [
                r"\n\s*(?:\d+\.?\s+)?(?:conclusion|conclusions?|summary)\s*\n",
                r"\n\s*(?:\d+\.?\s+)?(?:結論|まとめ)\s*\n"
            ],
            "references": [
                r"\n\s*(?:references|bibliography)\s*\n",
                r"\n\s*(?:参考文献|文献)\s*\n"
            ]
        }

        # テキストを小文字化（パターンマッチング用）
        text_lower = text.lower()

        # セクション境界を検出
        section_boundaries: list[tuple[int, str]] = []

        for section_name, patterns in section_patterns.items():
            for pattern in patterns:
                matches = list(re.finditer(pattern, text_lower, re.IGNORECASE))
                if matches:
                    # 最初のマッチを使用
                    match = matches[0]
                    section_boundaries.append((match.start(), section_name))
                    break

        # 位置でソート
        section_boundaries.sort(key=lambda x: x[0])

        # セクションテキストを抽出
        sections = {}

        if not section_boundaries:
            # セクションが検出されない場合は全体を"full_text"として扱う
            logger.warning("No IMRaD sections detected, using full text")
            sections["full_text"] = text
        else:
            for i, (start_pos, section_name) in enumerate(section_boundaries):
                # 次のセクションの開始位置を取得
                if i + 1 < len(section_boundaries):
                    end_pos = section_boundaries[i + 1][0]
                else:
                    end_pos = len(text)

                # セクションテキストを抽出
                section_text = text[start_pos:end_pos].strip()
                sections[section_name] = section_text

        logger.debug(f"Detected sections: {list(sections.keys())}")

        return sections

    def _chunk_text(self, text: str, chunk_size: int = 512) -> list[str]:
        """テキストをチャンク化

        文単位で分割し、chunk_size以下に収めます。
        文の途中で切らないように配慮します。

        Args:
            text: チャンク化するテキスト
            chunk_size: チャンクサイズ（文字数）

        Returns:
            チャンクのリスト

        Requirements: 2.1
        """
        if not text.strip():
            return []

        # 文単位で分割（英語と日本語の両方に対応）
        # 英語: ". ", "! ", "? " で分割
        # 日本語: "。", "！", "？" で分割
        sentence_delimiters = r'(?<=[.!?。！？])\s+'
        sentences = re.split(sentence_delimiters, text)

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # 現在のチャンクに文を追加できるか確認
            if len(current_chunk) + len(sentence) + 1 <= chunk_size:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                # 現在のチャンクを保存
                if current_chunk:
                    chunks.append(current_chunk)

                # 文が単独でchunk_sizeを超える場合
                if len(sentence) > chunk_size:
                    # 強制的に分割
                    for i in range(0, len(sentence), chunk_size):
                        chunks.append(sentence[i:i + chunk_size])
                    current_chunk = ""
                else:
                    current_chunk = sentence

        # 最後のチャンクを追加
        if current_chunk:
            chunks.append(current_chunk)

        logger.debug(f"Chunked text into {len(chunks)} chunks (chunk_size={chunk_size})")

        return chunks


async def basic_rag_query(
    question: str,
    arxiv_ids: Optional[list[str]],
    chroma_client: ChromaClient,
    embedding_service: EmbeddingService,
    llm_service: LLMService,
    top_k: int = 5
) -> RAGResponse:
    """基本的なRAG処理

    ベクター検索→コンテキスト構築→LLM推論の基本フローを実行します。

    Args:
        question: ユーザーの質問
        arxiv_ids: フィルタリングする論文IDリスト（Noneの場合は全論文を対象）
        chroma_client: Chromaクライアント
        embedding_service: Embeddingサービス
        llm_service: LLMサービス
        top_k: 取得する検索結果数

    Returns:
        RAG回答（answer、sources、metadata）

    Requirements: 2.4, 2.5
    """
    try:
        logger.info(
            f"Starting basic RAG query: question='{question[:50]}...', "
            f"arxiv_ids={arxiv_ids}, top_k={top_k}"
        )

        # 1. ベクター検索
        logger.debug("Step 1: Vector search")
        query_embedding = await embedding_service.embed(question)
        results = chroma_client.search(
            query_embedding=query_embedding,
            arxiv_ids=arxiv_ids,
            top_k=top_k
        )

        if not results:
            logger.warning("No search results found")
            return RAGResponse(
                answer="申し訳ございません。関連する情報が見つかりませんでした。",
                sources=[],
                metadata={"results_found": 0}
            )

        logger.info(f"Found {len(results)} search results")

        # 2. コンテキスト構築
        logger.debug("Step 2: Building context")
        context = build_context(results)
        logger.debug(f"Context built: length={len(context)} chars")

        # 3. LLM推論
        logger.debug("Step 3: LLM generation")
        answer = await llm_service.generate(question, context)
        logger.info(f"Answer generated: length={len(answer)} chars")

        # 4. レスポンス構築
        response = RAGResponse(
            answer=answer,
            sources=results,
            metadata={
                "results_found": len(results),
                "context_length": len(context)
            }
        )

        logger.info("Basic RAG query completed successfully")
        return response

    except Exception as e:
        logger.error(f"Failed to execute basic RAG query: {e}")
        raise


def build_context(results: list[SearchResult]) -> str:
    """検索結果からコンテキスト文字列を構築

    SearchResultsのリストから、LLMに渡すコンテキスト文字列を構築します。
    各チャンクのテキストとメタデータ（論文タイトル、セクション）を含めます。

    Args:
        results: 検索結果のリスト

    Returns:
        構築されたコンテキスト文字列

    Requirements: 2.4, 2.5
    """
    if not results:
        return ""

    context_parts = []

    for i, result in enumerate(results, 1):
        # メタデータから情報を取得
        title = result.metadata.get("title", "Unknown")
        section = result.metadata.get("section", "unknown")
        arxiv_id = result.metadata.get("arxiv_id", "unknown")

        # コンテキストパートを構築
        context_part = f"""[文献 {i}] {title} (arXiv: {arxiv_id}, セクション: {section})
{result.text}
"""
        context_parts.append(context_part)

    # 全てのパートを結合
    context = "\n".join(context_parts)

    logger.debug(
        f"Built context from {len(results)} results, "
        f"total length: {len(context)} chars"
    )

    return context
