# -*- coding: utf-8 -*-
"""PaperMetadataモデルのユニットテスト

Requirements: 1.5, 2.3
"""

import pytest
import json
from datetime import datetime
from pydantic import ValidationError

from src.models.paper import PaperMetadata


# ========================================
# Validation tests
# ========================================

def test_paper_metadata_valid():
    """有効なデータでPaperMetadataを作成"""
    data = {
        "arxiv_id": "2301.00001",
        "title": "Test Paper",
        "authors": ["Author One", "Author Two"],
        "abstract": "This is a test abstract.",
        "year": 2023,
        "categories": ["cs.AI", "cs.LG"],
        "pdf_url": "https://arxiv.org/pdf/2301.00001.pdf",
        "doi": "10.1234/test",
        "published_date": datetime(2023, 1, 1)
    }
    
    paper = PaperMetadata(**data)
    
    assert paper.arxiv_id == "2301.00001"
    assert paper.title == "Test Paper"
    assert paper.authors == ["Author One", "Author Two"]
    assert paper.abstract == "This is a test abstract."
    assert paper.year == 2023
    assert paper.categories == ["cs.AI", "cs.LG"]
    assert paper.pdf_url == "https://arxiv.org/pdf/2301.00001.pdf"
    assert paper.doi == "10.1234/test"
    assert paper.published_date == datetime(2023, 1, 1)


def test_paper_metadata_without_doi():
    """DOIなしでPaperMetadataを作成"""
    data = {
        "arxiv_id": "2301.00001",
        "title": "Test Paper",
        "authors": ["Author One"],
        "abstract": "Abstract",
        "year": 2023,
        "categories": ["cs.AI"],
        "pdf_url": "https://arxiv.org/pdf/2301.00001.pdf",
        "published_date": datetime(2023, 1, 1)
    }
    
    paper = PaperMetadata(**data)
    
    assert paper.doi is None


def test_paper_metadata_missing_required_field():
    """必須フィールドが欠けている場合はエラー"""
    data = {
        "arxiv_id": "2301.00001",
        "title": "Test Paper",
        # authors が欠けている
        "abstract": "Abstract",
        "year": 2023,
        "categories": ["cs.AI"],
        "pdf_url": "https://arxiv.org/pdf/2301.00001.pdf",
        "published_date": datetime(2023, 1, 1)
    }
    
    with pytest.raises(ValidationError):
        PaperMetadata(**data)


def test_paper_metadata_coerces_year_from_string():
    """yearが文字列の場合は自動的に整数に変換される（Pydantic v2）"""
    data = {
        "arxiv_id": "2301.00001",
        "title": "Test Paper",
        "authors": ["Author One"],
        "abstract": "Abstract",
        "year": "2023",  # 文字列
        "categories": ["cs.AI"],
        "pdf_url": "https://arxiv.org/pdf/2301.00001.pdf",
        "published_date": datetime(2023, 1, 1)
    }
    
    paper = PaperMetadata(**data)
    assert paper.year == 2023
    assert isinstance(paper.year, int)


def test_paper_metadata_invalid_authors_type():
    """authorsが文字列の場合はエラー"""
    data = {
        "arxiv_id": "2301.00001",
        "title": "Test Paper",
        "authors": "Author One",  # 文字列（リストではない）
        "abstract": "Abstract",
        "year": 2023,
        "categories": ["cs.AI"],
        "pdf_url": "https://arxiv.org/pdf/2301.00001.pdf",
        "published_date": datetime(2023, 1, 1)
    }
    
    with pytest.raises(ValidationError):
        PaperMetadata(**data)


def test_paper_metadata_empty_authors():
    """空の著者リスト"""
    data = {
        "arxiv_id": "2301.00001",
        "title": "Test Paper",
        "authors": [],  # 空リスト
        "abstract": "Abstract",
        "year": 2023,
        "categories": ["cs.AI"],
        "pdf_url": "https://arxiv.org/pdf/2301.00001.pdf",
        "published_date": datetime(2023, 1, 1)
    }
    
    paper = PaperMetadata(**data)
    assert paper.authors == []


# ========================================
# Serialization tests
# ========================================

def test_paper_metadata_to_dict():
    """PaperMetadataをdictに変換"""
    paper = PaperMetadata(
        arxiv_id="2301.00001",
        title="Test Paper",
        authors=["Author One"],
        abstract="Abstract",
        year=2023,
        categories=["cs.AI"],
        pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
        published_date=datetime(2023, 1, 1)
    )
    
    data = paper.model_dump()
    
    assert isinstance(data, dict)
    assert data["arxiv_id"] == "2301.00001"
    assert data["title"] == "Test Paper"
    assert data["authors"] == ["Author One"]


def test_paper_metadata_to_json():
    """PaperMetadataをJSONに変換"""
    paper = PaperMetadata(
        arxiv_id="2301.00001",
        title="Test Paper",
        authors=["Author One"],
        abstract="Abstract",
        year=2023,
        categories=["cs.AI"],
        pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
        published_date=datetime(2023, 1, 1)
    )
    
    json_str = paper.model_dump_json()
    
    assert isinstance(json_str, str)
    data = json.loads(json_str)
    assert data["arxiv_id"] == "2301.00001"


def test_paper_metadata_from_dict():
    """dictからPaperMetadataを作成"""
    data = {
        "arxiv_id": "2301.00001",
        "title": "Test Paper",
        "authors": ["Author One"],
        "abstract": "Abstract",
        "year": 2023,
        "categories": ["cs.AI"],
        "pdf_url": "https://arxiv.org/pdf/2301.00001.pdf",
        "published_date": "2023-01-01T00:00:00"
    }
    
    paper = PaperMetadata(**data)
    
    assert paper.arxiv_id == "2301.00001"
    assert paper.published_date == datetime(2023, 1, 1)


def test_paper_metadata_round_trip():
    """シリアライズ→デシリアライズのラウンドトリップ"""
    original = PaperMetadata(
        arxiv_id="2301.00001",
        title="Test Paper",
        authors=["Author One", "Author Two"],
        abstract="Abstract",
        year=2023,
        categories=["cs.AI", "cs.LG"],
        pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
        doi="10.1234/test",
        published_date=datetime(2023, 1, 1, 12, 30, 45)
    )
    
    # dict経由
    data = original.model_dump()
    restored = PaperMetadata(**data)
    
    assert restored.arxiv_id == original.arxiv_id
    assert restored.title == original.title
    assert restored.authors == original.authors
    assert restored.published_date == original.published_date


# ========================================
# Edge cases
# ========================================

def test_paper_metadata_with_special_characters():
    """特殊文字を含むデータ"""
    paper = PaperMetadata(
        arxiv_id="2301.00001",
        title="Test Paper: A Novel Approach (2023)",
        authors=["Author O'Brien", "Author-Smith"],
        abstract="Abstract with \"quotes\" and 'apostrophes'.",
        year=2023,
        categories=["cs.AI"],
        pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
        published_date=datetime(2023, 1, 1)
    )
    
    assert "O'Brien" in paper.authors[0]
    assert "quotes" in paper.abstract


def test_paper_metadata_with_unicode():
    """Unicode文字を含むデータ"""
    paper = PaperMetadata(
        arxiv_id="2301.00001",
        title="日本語タイトル",
        authors=["山田太郎", "田中花子"],
        abstract="これは日本語の要旨です。",
        year=2023,
        categories=["cs.AI"],
        pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
        published_date=datetime(2023, 1, 1)
    )
    
    assert paper.title == "日本語タイトル"
    assert "山田太郎" in paper.authors
