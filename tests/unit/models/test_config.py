# -*- coding: utf-8 -*-
"""設定モデルのユニットテスト

Requirements: 2.3
"""

import pytest
import json
from pathlib import Path
from pydantic import ValidationError

from src.models.config import ChromaConfig, LLMConfig, EmbeddingConfig


# ========================================
# ChromaConfig tests
# ========================================

def test_chroma_config_defaults():
    """デフォルト値でChromaConfigを作成"""
    config = ChromaConfig()
    
    assert config.persist_dir == Path("./data/chroma")
    assert config.collection_name == "papersmith_papers"
    assert config.distance_metric == "cosine"


def test_chroma_config_custom_values():
    """カスタム値でChromaConfigを作成"""
    config = ChromaConfig(
        persist_dir=Path("/custom/path"),
        collection_name="custom_collection",
        distance_metric="l2"
    )
    
    assert config.persist_dir == Path("/custom/path")
    assert config.collection_name == "custom_collection"
    assert config.distance_metric == "l2"


def test_chroma_config_to_dict():
    """ChromaConfigをdictに変換"""
    config = ChromaConfig()
    data = config.model_dump()
    
    assert isinstance(data, dict)
    assert "persist_dir" in data
    assert "collection_name" in data


def test_chroma_config_to_json():
    """ChromaConfigをJSONに変換"""
    config = ChromaConfig()
    json_str = config.model_dump_json()
    
    assert isinstance(json_str, str)
    data = json.loads(json_str)
    assert "collection_name" in data


# ========================================
# LLMConfig tests
# ========================================

def test_llm_config_defaults():
    """デフォルト値でLLMConfigを作成"""
    config = LLMConfig()
    
    assert config.backend == "gemini"
    assert config.gemini_model_name == "gemini-2.0-flash"
    assert config.openai_model_name == "gpt-4o-mini"
    assert config.local_model_name == "elyza/Llama-3-ELYZA-JP-8B"
    assert config.max_length == 512
    assert config.temperature == 0.7


def test_llm_config_gemini_backend():
    """Geminiバックエンドの設定"""
    config = LLMConfig(
        backend="gemini",
        gemini_api_key="test-api-key",
        gemini_model_name="gemini-1.5-pro"
    )
    
    assert config.backend == "gemini"
    assert config.gemini_api_key == "test-api-key"
    assert config.gemini_model_name == "gemini-1.5-pro"


def test_llm_config_openai_backend():
    """OpenAIバックエンドの設定"""
    config = LLMConfig(
        backend="openai",
        openai_api_key="test-api-key",
        openai_model_name="gpt-4"
    )
    
    assert config.backend == "openai"
    assert config.openai_api_key == "test-api-key"
    assert config.openai_model_name == "gpt-4"


def test_llm_config_local_backend():
    """ローカルバックエンドの設定"""
    config = LLMConfig(
        backend="local-cuda",
        local_model_name="custom/model"
    )
    
    assert config.backend == "local-cuda"
    assert config.local_model_name == "custom/model"


def test_llm_config_generation_settings():
    """生成設定のカスタマイズ"""
    config = LLMConfig(
        max_length=1024,
        temperature=0.9
    )
    
    assert config.max_length == 1024
    assert config.temperature == 0.9


def test_llm_config_to_dict():
    """LLMConfigをdictに変換"""
    config = LLMConfig()
    data = config.model_dump()
    
    assert isinstance(data, dict)
    assert "backend" in data
    assert "max_length" in data


def test_llm_config_to_json():
    """LLMConfigをJSONに変換"""
    config = LLMConfig()
    json_str = config.model_dump_json()
    
    assert isinstance(json_str, str)
    data = json.loads(json_str)
    assert "backend" in data


# ========================================
# EmbeddingConfig tests
# ========================================

def test_embedding_config_defaults():
    """デフォルト値でEmbeddingConfigを作成"""
    config = EmbeddingConfig()
    
    assert config.backend == "gemini"
    assert config.openai_embedding_model == "text-embedding-3-small"
    assert config.local_model_name == "intfloat/multilingual-e5-base"
    assert config.batch_size == 32
    assert config.normalize_embeddings is True


def test_embedding_config_gemini_backend():
    """Geminiバックエンドの設定"""
    config = EmbeddingConfig(
        backend="gemini",
        gemini_api_key="test-api-key"
    )
    
    assert config.backend == "gemini"
    assert config.gemini_api_key == "test-api-key"


def test_embedding_config_openai_backend():
    """OpenAIバックエンドの設定"""
    config = EmbeddingConfig(
        backend="openai",
        openai_api_key="test-api-key",
        openai_embedding_model="text-embedding-3-large"
    )
    
    assert config.backend == "openai"
    assert config.openai_api_key == "test-api-key"
    assert config.openai_embedding_model == "text-embedding-3-large"


def test_embedding_config_local_backend():
    """ローカルバックエンドの設定"""
    config = EmbeddingConfig(
        backend="local-cpu",
        local_model_name="custom/embedding-model"
    )
    
    assert config.backend == "local-cpu"
    assert config.local_model_name == "custom/embedding-model"


def test_embedding_config_batch_settings():
    """バッチ設定のカスタマイズ"""
    config = EmbeddingConfig(
        batch_size=64,
        normalize_embeddings=False
    )
    
    assert config.batch_size == 64
    assert config.normalize_embeddings is False


def test_embedding_config_to_dict():
    """EmbeddingConfigをdictに変換"""
    config = EmbeddingConfig()
    data = config.model_dump()
    
    assert isinstance(data, dict)
    assert "backend" in data
    assert "batch_size" in data


def test_embedding_config_to_json():
    """EmbeddingConfigをJSONに変換"""
    config = EmbeddingConfig()
    json_str = config.model_dump_json()
    
    assert isinstance(json_str, str)
    data = json.loads(json_str)
    assert "backend" in data


# ========================================
# Round trip tests
# ========================================

def test_chroma_config_round_trip():
    """ChromaConfigのラウンドトリップ"""
    original = ChromaConfig(
        persist_dir=Path("/test/path"),
        collection_name="test_collection",
        distance_metric="l2"
    )
    
    data = original.model_dump()
    restored = ChromaConfig(**data)
    
    assert restored.persist_dir == original.persist_dir
    assert restored.collection_name == original.collection_name
    assert restored.distance_metric == original.distance_metric


def test_llm_config_round_trip():
    """LLMConfigのラウンドトリップ"""
    original = LLMConfig(
        backend="openai",
        openai_api_key="test-key",
        max_length=1024,
        temperature=0.8
    )
    
    data = original.model_dump()
    restored = LLMConfig(**data)
    
    assert restored.backend == original.backend
    assert restored.openai_api_key == original.openai_api_key
    assert restored.max_length == original.max_length
    assert restored.temperature == original.temperature


def test_embedding_config_round_trip():
    """EmbeddingConfigのラウンドトリップ"""
    original = EmbeddingConfig(
        backend="local-mlx",
        local_model_name="custom/model",
        batch_size=16,
        normalize_embeddings=False
    )
    
    data = original.model_dump()
    restored = EmbeddingConfig(**data)
    
    assert restored.backend == original.backend
    assert restored.local_model_name == original.local_model_name
    assert restored.batch_size == original.batch_size
    assert restored.normalize_embeddings == original.normalize_embeddings


# ========================================
# Edge cases
# ========================================

def test_chroma_config_with_relative_path():
    """相対パスでChromaConfigを作成"""
    config = ChromaConfig(persist_dir=Path("./relative/path"))
    
    assert config.persist_dir == Path("./relative/path")


def test_llm_config_with_none_api_keys():
    """APIキーがNoneの場合"""
    config = LLMConfig(
        gemini_api_key=None,
        openai_api_key=None
    )
    
    assert config.gemini_api_key is None
    assert config.openai_api_key is None


def test_embedding_config_with_none_api_keys():
    """APIキーがNoneの場合"""
    config = EmbeddingConfig(
        gemini_api_key=None,
        openai_api_key=None
    )
    
    assert config.gemini_api_key is None
    assert config.openai_api_key is None


def test_llm_config_all_backends():
    """すべてのバックエンドタイプ"""
    backends = ["gemini", "openai", "local-cpu", "local-mlx", "local-cuda"]
    
    for backend in backends:
        config = LLMConfig(backend=backend)
        assert config.backend == backend


def test_embedding_config_all_backends():
    """すべてのバックエンドタイプ"""
    backends = ["gemini", "openai", "local-cpu", "local-mlx", "local-cuda"]
    
    for backend in backends:
        config = EmbeddingConfig(backend=backend)
        assert config.backend == backend
