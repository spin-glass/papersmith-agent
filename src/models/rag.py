"""RAG関連モデル"""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class SearchResult(BaseModel):
    """検索結果

    Requirements: 2.3
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chunk_id": "2301.00001_introduction_0",
                "text": "This paper presents a novel approach...",
                "score": 0.85,
                "metadata": {
                    "arxiv_id": "2301.00001",
                    "title": "Example Paper",
                    "authors": "Author One, Author Two",
                    "year": 2023,
                    "section": "introduction"
                }
            }
        }
    )

    chunk_id: str = Field(..., description="チャンクID")
    text: str = Field(..., description="チャンクテキスト")
    score: float = Field(..., description="類似度スコア")
    metadata: dict[str, Any] = Field(..., description="メタデータ")


class RAGResponse(BaseModel):
    """RAG回答

    Requirements: 2.3
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "answer": "この論文では、新しいアプローチを提案しています...",
                "sources": [
                    {
                        "chunk_id": "2301.00001_introduction_0",
                        "text": "This paper presents...",
                        "score": 0.85,
                        "metadata": {"arxiv_id": "2301.00001"}
                    }
                ],
                "metadata": {
                    "support_score": 0.75,
                    "attempts": 1
                }
            }
        }
    )

    answer: str = Field(..., description="生成された回答")
    sources: list[SearchResult] = Field(..., description="参照元の検索結果")
    metadata: Optional[dict[str, Any]] = Field(None, description="追加メタデータ")
