"""論文メタデータモデル"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PaperMetadata(BaseModel):
    """論文メタデータ

    Requirements: 1.5, 2.3
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "arxiv_id": "2301.00001",
                "title": "Example Paper Title",
                "authors": ["Author One", "Author Two"],
                "abstract": "This is an example abstract.",
                "year": 2023,
                "categories": ["cs.AI", "cs.LG"],
                "pdf_url": "https://arxiv.org/pdf/2301.00001.pdf",
                "doi": "10.1234/example",
                "published_date": "2023-01-01T00:00:00Z"
            }
        }
    )

    arxiv_id: str = Field(..., description="arXiv論文ID")
    title: str = Field(..., description="論文タイトル")
    authors: list[str] = Field(..., description="著者リスト")
    abstract: str = Field(..., description="論文要旨")
    year: int = Field(..., description="発行年")
    categories: list[str] = Field(..., description="arXivカテゴリ")
    pdf_url: str = Field(..., description="PDF URL")
    doi: Optional[str] = Field(None, description="DOI")
    published_date: datetime = Field(..., description="公開日時")
