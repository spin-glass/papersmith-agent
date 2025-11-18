"""Chromaクライアント

Requirements: 2.2, 2.3, 2.4
"""

import logging
from typing import Any, Optional

import chromadb
from chromadb.config import Settings

from src.models.config import ChromaConfig
from src.models.rag import SearchResult

logger = logging.getLogger(__name__)


class ChromaClient:
    """Chromaベクターデータベースクライアント

    Requirements:
    - 2.2: Embedding生成とChromaベクターストアへの保存
    - 2.3: メタデータ（arxiv_id、title、authors、year、section、chunk_id）を含める
    - 2.4: Chromaベクターストアから関連チャンクを検索
    """

    def __init__(self, config: ChromaConfig):
        """初期化

        Args:
            config: Chroma設定
        """
        self.config = config
        self.client: Optional[chromadb.ClientAPI] = None
        self.collection: Optional[chromadb.Collection] = None

    def initialize(self) -> None:
        """Chromaクライアントとコレクションを初期化

        コレクション作成と永続化ディレクトリ設定を行う。

        Requirements: 2.2, 2.3
        """
        try:
            # 永続化ディレクトリを作成
            self.config.persist_dir.mkdir(parents=True, exist_ok=True)

            # Chromaクライアントを初期化
            self.client = chromadb.PersistentClient(
                path=str(self.config.persist_dir),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # コレクションを取得または作成
            self.collection = self.client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={"hnsw:space": self.config.distance_metric}
            )

            logger.info(
                f"Chroma initialized: collection='{self.config.collection_name}', "
                f"persist_dir='{self.config.persist_dir}', "
                f"documents={self.count()}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize Chroma: {e}")
            raise

    def add(
        self,
        embedding: list[float],
        text: str,
        metadata: dict[str, Any],
        chunk_id: Optional[str] = None
    ) -> None:
        """ドキュメントをChromaに追加

        Args:
            embedding: Embeddingベクター
            text: チャンクテキスト
            metadata: メタデータ（arxiv_id、title、authors、year、section、chunk_id等）
            chunk_id: チャンクID（指定しない場合はmetadataから取得）

        Requirements: 2.2, 2.3
        """
        if self.collection is None:
            raise RuntimeError("Chroma not initialized. Call initialize() first.")

        # chunk_idを決定
        if chunk_id is None:
            chunk_id = metadata.get("chunk_id")
            if chunk_id is None:
                raise ValueError("chunk_id must be provided either as argument or in metadata")

        # メタデータを文字列化（Chromaは文字列、数値、boolのみサポート）
        processed_metadata = self._process_metadata(metadata)

        try:
            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[processed_metadata]
            )

            logger.debug(f"Added document: chunk_id='{chunk_id}'")

        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            raise

    def search(
        self,
        query_embedding: list[float],
        arxiv_ids: Optional[list[str]] = None,
        top_k: int = 5
    ) -> list[SearchResult]:
        """ベクター検索を実行

        Args:
            query_embedding: クエリのEmbeddingベクター
            arxiv_ids: フィルタリングする論文IDリスト（Noneの場合は全論文を対象）
            top_k: 取得する結果数

        Returns:
            検索結果のリスト

        Requirements: 2.3, 2.4
        """
        if self.collection is None:
            raise RuntimeError("Chroma not initialized. Call initialize() first.")

        try:
            # where句を構築（arxiv_idsフィルタ）
            where_clause = None
            if arxiv_ids is not None and len(arxiv_ids) > 0:
                if len(arxiv_ids) == 1:
                    where_clause = {"arxiv_id": arxiv_ids[0]}
                else:
                    where_clause = {"arxiv_id": {"$in": arxiv_ids}}

            # ベクター検索を実行
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )

            # SearchResultに変換
            search_results = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    chunk_id = results["ids"][0][i]
                    text = results["documents"][0][i]
                    distance = results["distances"][0][i]
                    metadata = results["metadatas"][0][i]

                    # 距離をスコアに変換（cosine距離の場合: score = 1 - distance）
                    score = 1.0 - distance if distance is not None else 0.0

                    search_results.append(
                        SearchResult(
                            chunk_id=chunk_id,
                            text=text,
                            score=score,
                            metadata=metadata
                        )
                    )

            logger.debug(
                f"Search completed: query_embedding_dim={len(query_embedding)}, "
                f"arxiv_ids={arxiv_ids}, top_k={top_k}, results={len(search_results)}"
            )

            return search_results

        except Exception as e:
            logger.error(f"Failed to search: {e}")
            raise

    def count(self) -> int:
        """インデックス内のドキュメント数を取得

        Returns:
            ドキュメント数

        Requirements: 2.3
        """
        if self.collection is None:
            raise RuntimeError("Chroma not initialized. Call initialize() first.")

        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            raise

    def _process_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """メタデータをChroma互換形式に変換

        Chromaは文字列、数値、boolのみサポートするため、
        リストや複雑な型を文字列に変換する。

        Args:
            metadata: 元のメタデータ

        Returns:
            処理済みメタデータ
        """
        processed = {}

        for key, value in metadata.items():
            if value is None:
                continue
            elif isinstance(value, (str, int, float, bool)):
                processed[key] = value
            elif isinstance(value, list):
                # リストはカンマ区切り文字列に変換
                processed[key] = ", ".join(str(v) for v in value)
            else:
                # その他の型は文字列に変換
                processed[key] = str(value)

        return processed

    def reset(self) -> None:
        """コレクションをリセット（全データ削除）

        注意: この操作は元に戻せません。
        """
        if self.client is None:
            raise RuntimeError("Chroma not initialized. Call initialize() first.")

        try:
            self.client.delete_collection(name=self.config.collection_name)
            logger.warning(f"Collection '{self.config.collection_name}' deleted")

            # コレクションを再作成
            self.collection = self.client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={"hnsw:space": self.config.distance_metric}
            )
            logger.info(f"Collection '{self.config.collection_name}' recreated")

        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            raise
