# -*- coding: utf-8 -*-
"""RAGモデルのユニットテスト

Requirements: 2.3
"""

import pytest
import json
from pydantic import ValidationError

from src.models.rag import SearchResult, RAGResponse


# ========================================
# SearchResult tests
# ========================================

def test_search_result_valid():
    """有効なデータでSearchResultを作成"""
    data = {
        "chunk_id": "2301.00001_intro_0",
        "text": "This is test text.",
        "score": 0.85,
        "metadata": {
            "arxiv_id": "2301.00001",
            "title": "Test Paper",
            "section": "introduction"
        }
    }
    
    result = SearchResult(**data)
    
    assert result.chunk_id == "2301.00001_intro_0"
    assert result.text == "This is test text."
    assert result.score == 0.85
    assert result.metadata["arxiv_id"] == "2301.00001"


def test_search_result_missing_required_field():
    """必須フィールドが欠けている場合はエラー"""
    data = {
        "chunk_id": "2301.00001_intro_0",
        "text": "This is test text.",
        # score が欠けている
        "metadata": {"arxiv_id": "2301.00001"}
    }
    
    with pytest.raises(ValidationError):
        SearchResult(**data)


def test_search_result_coerces_score_from_string():
    """scoreが文字列の場合は自動的にfloatに変換される（Pydantic v2）"""
    data = {
        "chunk_id": "2301.00001_intro_0",
        "text": "This is test text.",
        "score": "0.85",  # 文字列
        "metadata": {"arxiv_id": "2301.00001"}
    }
    
    result = SearchResult(**data)
    assert result.score == 0.85
    assert isinstance(result.score, float)


def test_search_result_empty_metadata():
    """空のメタデータ"""
    result = SearchResult(
        chunk_id="test_chunk",
        text="Test text",
        score=0.5,
        metadata={}
    )
    
    assert result.metadata == {}


def test_search_result_to_dict():
    """SearchResultをdictに変換"""
    result = SearchResult(
        chunk_id="test_chunk",
        text="Test text",
        score=0.75,
        metadata={"key": "value"}
    )
    
    data = result.model_dump()
    
    assert isinstance(data, dict)
    assert data["chunk_id"] == "test_chunk"
    assert data["score"] == 0.75


def test_search_result_to_json():
    """SearchResultをJSONに変換"""
    result = SearchResult(
        chunk_id="test_chunk",
        text="Test text",
        score=0.75,
        metadata={"key": "value"}
    )
    
    json_str = result.model_dump_json()
    
    assert isinstance(json_str, str)
    data = json.loads(json_str)
    assert data["chunk_id"] == "test_chunk"


# ========================================
# RAGResponse tests
# ========================================

def test_rag_response_valid():
    """有効なデータでRAGResponseを作成"""
    source = SearchResult(
        chunk_id="test_chunk",
        text="Source text",
        score=0.85,
        metadata={"arxiv_id": "2301.00001"}
    )
    
    response = RAGResponse(
        answer="This is the answer.",
        sources=[source],
        metadata={"support_score": 0.75}
    )
    
    assert response.answer == "This is the answer."
    assert len(response.sources) == 1
    assert response.sources[0].chunk_id == "test_chunk"
    assert response.metadata["support_score"] == 0.75


def test_rag_response_without_metadata():
    """metadataなしでRAGResponseを作成"""
    source = SearchResult(
        chunk_id="test_chunk",
        text="Source text",
        score=0.85,
        metadata={}
    )
    
    response = RAGResponse(
        answer="Answer",
        sources=[source]
    )
    
    assert response.metadata is None


def test_rag_response_empty_sources():
    """空のsourcesリスト"""
    response = RAGResponse(
        answer="Answer with no sources",
        sources=[]
    )
    
    assert len(response.sources) == 0


def test_rag_response_multiple_sources():
    """複数のsources"""
    sources = [
        SearchResult(
            chunk_id=f"chunk_{i}",
            text=f"Text {i}",
            score=0.8 - i * 0.1,
            metadata={"index": i}
        )
        for i in range(3)
    ]
    
    response = RAGResponse(
        answer="Answer from multiple sources",
        sources=sources
    )
    
    assert len(response.sources) == 3
    assert response.sources[0].chunk_id == "chunk_0"
    # 浮動小数点の比較は近似値で
    assert abs(response.sources[2].score - 0.6) < 0.0001


def test_rag_response_missing_required_field():
    """必須フィールドが欠けている場合はエラー"""
    data = {
        "answer": "Answer",
        # sources が欠けている
    }
    
    with pytest.raises(ValidationError):
        RAGResponse(**data)


def test_rag_response_invalid_sources_type():
    """sourcesが正しい型でない場合はエラー"""
    data = {
        "answer": "Answer",
        "sources": "not a list"  # 文字列
    }
    
    with pytest.raises(ValidationError):
        RAGResponse(**data)


def test_rag_response_to_dict():
    """RAGResponseをdictに変換"""
    source = SearchResult(
        chunk_id="test_chunk",
        text="Text",
        score=0.8,
        metadata={}
    )
    
    response = RAGResponse(
        answer="Answer",
        sources=[source],
        metadata={"key": "value"}
    )
    
    data = response.model_dump()
    
    assert isinstance(data, dict)
    assert data["answer"] == "Answer"
    assert len(data["sources"]) == 1
    assert data["metadata"]["key"] == "value"


def test_rag_response_to_json():
    """RAGResponseをJSONに変換"""
    source = SearchResult(
        chunk_id="test_chunk",
        text="Text",
        score=0.8,
        metadata={}
    )
    
    response = RAGResponse(
        answer="Answer",
        sources=[source]
    )
    
    json_str = response.model_dump_json()
    
    assert isinstance(json_str, str)
    data = json.loads(json_str)
    assert data["answer"] == "Answer"


def test_rag_response_round_trip():
    """シリアライズ→デシリアライズのラウンドトリップ"""
    original = RAGResponse(
        answer="Original answer",
        sources=[
            SearchResult(
                chunk_id="chunk_1",
                text="Text 1",
                score=0.9,
                metadata={"key": "value"}
            )
        ],
        metadata={"support_score": 0.85, "attempts": 1}
    )
    
    # dict経由
    data = original.model_dump()
    restored = RAGResponse(**data)
    
    assert restored.answer == original.answer
    assert len(restored.sources) == len(original.sources)
    assert restored.sources[0].chunk_id == original.sources[0].chunk_id
    assert restored.metadata == original.metadata


# ========================================
# Edge cases
# ========================================

def test_search_result_with_special_characters():
    """特殊文字を含むテキスト"""
    result = SearchResult(
        chunk_id="test_chunk",
        text="Text with \"quotes\" and 'apostrophes'.",
        score=0.75,
        metadata={"key": "value with spaces"}
    )
    
    assert "quotes" in result.text


def test_search_result_with_unicode():
    """Unicode文字を含むテキスト"""
    result = SearchResult(
        chunk_id="test_chunk",
        text="日本語のテキスト",
        score=0.75,
        metadata={"title": "日本語タイトル"}
    )
    
    assert result.text == "日本語のテキスト"
    assert result.metadata["title"] == "日本語タイトル"


def test_rag_response_with_unicode():
    """Unicode文字を含む回答"""
    source = SearchResult(
        chunk_id="test_chunk",
        text="日本語のソース",
        score=0.8,
        metadata={}
    )
    
    response = RAGResponse(
        answer="これは日本語の回答です。",
        sources=[source]
    )
    
    assert response.answer == "これは日本語の回答です。"
