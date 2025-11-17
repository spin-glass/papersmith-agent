# -*- coding: utf-8 -*-
"""マルチバックエンド統合テスト

Requirements: 12.2, 12.3

このテストは各バックエンドの切り替えと環境変数による設定をテストします。
実際のAPI呼び出しは行わず、バックエンドの初期化と設定のみをテストします。
"""

import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock

from src.services.llm_service import LLMService
from src.services.embedding_service import EmbeddingService
from src.models.config import LLMConfig, EmbeddingConfig


# ===== LLMバックエンドテスト =====

def test_llm_backend_gemini():
    """Geminiバックエンドの初期化テスト
    
    Requirements: 12.2, 12.3
    """
    config = LLMConfig(backend="gemini")
    service = LLMService(config)
    
    assert service.config.backend == "gemini"
    assert service.backend is None  # load_model前はNone


def test_llm_backend_openai():
    """OpenAIバックエンドの初期化テスト
    
    Requirements: 12.2, 12.3
    """
    config = LLMConfig(backend="openai")
    service = LLMService(config)
    
    assert service.config.backend == "openai"
    assert service.backend is None


def test_llm_backend_local_cpu():
    """Local CPUバックエンドの初期化テスト
    
    Requirements: 12.2, 12.3
    """
    config = LLMConfig(backend="local-cpu")
    service = LLMService(config)
    
    assert service.config.backend == "local-cpu"
    assert service.backend is None


def test_llm_backend_local_mlx():
    """Local MLXバックエンドの初期化テスト
    
    Requirements: 12.2, 12.3
    """
    config = LLMConfig(backend="local-mlx")
    service = LLMService(config)
    
    assert service.config.backend == "local-mlx"
    assert service.backend is None


def test_llm_backend_local_cuda():
    """Local CUDAバックエンドの初期化テスト
    
    Requirements: 12.2, 12.3
    """
    config = LLMConfig(backend="local-cuda")
    service = LLMService(config)
    
    assert service.config.backend == "local-cuda"
    assert service.backend is None


@pytest.mark.asyncio
async def test_llm_backend_switching():
    """LLMバックエンドの切り替えテスト
    
    Requirements: 12.2, 12.3
    """
    backends = ["gemini", "openai", "local-cpu", "local-mlx", "local-cuda"]
    
    for backend in backends:
        config = LLMConfig(backend=backend)
        service = LLMService(config)
        
        assert service.config.backend == backend
        assert not service.is_loaded()


def test_llm_env_var_configuration():
    """環境変数によるLLM設定テスト
    
    Requirements: 12.3
    """
    with patch.dict(os.environ, {"LLM_BACKEND": "openai"}):
        from src.utils.config_loader import load_llm_config
        config = load_llm_config()
        
        assert config.backend == "openai"


def test_llm_default_backend():
    """デフォルトLLMバックエンドのテスト
    
    Requirements: 12.3
    """
    # 環境変数をクリア
    with patch.dict(os.environ, {}, clear=True):
        from src.utils.config_loader import load_llm_config
        config = load_llm_config()
        
        # デフォルトはgemini
        assert config.backend == "gemini"


# ===== Embeddingバックエンドテスト =====

def test_embedding_backend_gemini():
    """Gemini Embeddingバックエンドの初期化テスト
    
    Requirements: 12.2, 12.3
    """
    config = EmbeddingConfig(backend="gemini")
    service = EmbeddingService(config)
    
    assert service.config.backend == "gemini"
    assert service.backend is None


def test_embedding_backend_openai():
    """OpenAI Embeddingバックエンドの初期化テスト
    
    Requirements: 12.2, 12.3
    """
    config = EmbeddingConfig(backend="openai")
    service = EmbeddingService(config)
    
    assert service.config.backend == "openai"
    assert service.backend is None


def test_embedding_backend_local_cpu():
    """Local CPU Embeddingバックエンドの初期化テスト
    
    Requirements: 12.2, 12.3
    """
    config = EmbeddingConfig(backend="local-cpu")
    service = EmbeddingService(config)
    
    assert service.config.backend == "local-cpu"
    assert service.backend is None


def test_embedding_backend_local_mlx():
    """Local MLX Embeddingバックエンドの初期化テスト
    
    Requirements: 12.2, 12.3
    """
    config = EmbeddingConfig(backend="local-mlx")
    service = EmbeddingService(config)
    
    assert service.config.backend == "local-mlx"
    assert service.backend is None


def test_embedding_backend_local_cuda():
    """Local CUDA Embeddingバックエンドの初期化テスト
    
    Requirements: 12.2, 12.3
    """
    config = EmbeddingConfig(backend="local-cuda")
    service = EmbeddingService(config)
    
    assert service.config.backend == "local-cuda"
    assert service.backend is None


@pytest.mark.asyncio
async def test_embedding_backend_switching():
    """Embeddingバックエンドの切り替えテスト
    
    Requirements: 12.2, 12.3
    """
    backends = ["gemini", "openai", "local-cpu", "local-mlx", "local-cuda"]
    
    for backend in backends:
        config = EmbeddingConfig(backend=backend)
        service = EmbeddingService(config)
        
        assert service.config.backend == backend
        assert not service.is_loaded()


def test_embedding_env_var_configuration():
    """環境変数によるEmbedding設定テスト
    
    Requirements: 12.3
    """
    with patch.dict(os.environ, {"EMBEDDING_BACKEND": "local-cpu"}):
        from src.utils.config_loader import load_embedding_config
        config = load_embedding_config()
        
        assert config.backend == "local-cpu"


def test_embedding_default_backend():
    """デフォルトEmbeddingバックエンドのテスト
    
    Requirements: 12.3
    """
    # 環境変数をクリア
    with patch.dict(os.environ, {}, clear=True):
        from src.utils.config_loader import load_embedding_config
        config = load_embedding_config()
        
        # デフォルトはgemini
        assert config.backend == "gemini"


# ===== 複合バックエンドテスト =====

def test_mixed_backends():
    """異なるバックエンドの組み合わせテスト
    
    Requirements: 12.2, 12.3
    """
    # LLMはGemini、EmbeddingはOpenAI
    llm_config = LLMConfig(backend="gemini")
    embedding_config = EmbeddingConfig(backend="openai")
    
    llm_service = LLMService(llm_config)
    embedding_service = EmbeddingService(embedding_config)
    
    assert llm_service.config.backend == "gemini"
    assert embedding_service.config.backend == "openai"


def test_all_local_backends():
    """すべてローカルバックエンドの組み合わせテスト
    
    Requirements: 12.2, 12.3
    """
    # LLMとEmbedding両方をローカルCPUに設定
    llm_config = LLMConfig(backend="local-cpu")
    embedding_config = EmbeddingConfig(backend="local-cpu")
    
    llm_service = LLMService(llm_config)
    embedding_service = EmbeddingService(embedding_config)
    
    assert llm_service.config.backend == "local-cpu"
    assert embedding_service.config.backend == "local-cpu"


def test_all_api_backends():
    """すべてAPIバックエンドの組み合わせテスト
    
    Requirements: 12.2, 12.3
    """
    # LLMとEmbedding両方をGeminiに設定
    llm_config = LLMConfig(backend="gemini")
    embedding_config = EmbeddingConfig(backend="gemini")
    
    llm_service = LLMService(llm_config)
    embedding_service = EmbeddingService(embedding_config)
    
    assert llm_service.config.backend == "gemini"
    assert embedding_service.config.backend == "gemini"


def test_env_var_mixed_configuration():
    """環境変数による混合設定テスト
    
    Requirements: 12.3
    """
    with patch.dict(os.environ, {
        "LLM_BACKEND": "openai",
        "EMBEDDING_BACKEND": "local-cpu"
    }):
        from src.utils.config_loader import load_llm_config, load_embedding_config
        
        llm_config = load_llm_config()
        embedding_config = load_embedding_config()
        
        assert llm_config.backend == "openai"
        assert embedding_config.backend == "local-cpu"


# ===== バックエンド設定の検証テスト =====

def test_llm_config_validation():
    """LLM設定のバリデーションテスト
    
    Requirements: 12.2
    """
    # 有効なバックエンド
    valid_backends = ["gemini", "openai", "local-cpu", "local-mlx", "local-cuda"]
    
    for backend in valid_backends:
        config = LLMConfig(backend=backend)
        assert config.backend == backend


def test_embedding_config_validation():
    """Embedding設定のバリデーションテスト
    
    Requirements: 12.2
    """
    # 有効なバックエンド
    valid_backends = ["gemini", "openai", "local-cpu", "local-mlx", "local-cuda"]
    
    for backend in valid_backends:
        config = EmbeddingConfig(backend=backend)
        assert config.backend == backend


def test_backend_specific_config():
    """バックエンド固有の設定テスト
    
    Requirements: 12.2, 12.3
    """
    # Gemini固有の設定
    gemini_llm_config = LLMConfig(
        backend="gemini",
        gemini_model_name="gemini-1.5-flash"
    )
    assert gemini_llm_config.gemini_model_name == "gemini-1.5-flash"
    
    # OpenAI固有の設定
    openai_llm_config = LLMConfig(
        backend="openai",
        openai_model_name="gpt-4"
    )
    assert openai_llm_config.openai_model_name == "gpt-4"
    
    # Local固有の設定
    local_llm_config = LLMConfig(
        backend="local-cpu",
        local_model_name="elyza/Llama-3-ELYZA-JP-8B"
    )
    assert local_llm_config.local_model_name == "elyza/Llama-3-ELYZA-JP-8B"


def test_backend_priority():
    """バックエンド優先順位のテスト
    
    Requirements: 12.3
    """
    # 環境変数が設定されている場合、それが優先される
    with patch.dict(os.environ, {"LLM_BACKEND": "openai"}):
        from src.utils.config_loader import load_llm_config
        config = load_llm_config()
        assert config.backend == "openai"
    
    # 環境変数がない場合、デフォルト値が使用される
    with patch.dict(os.environ, {}, clear=True):
        from src.utils.config_loader import load_llm_config
        config = load_llm_config()
        assert config.backend == "gemini"


@pytest.mark.asyncio
async def test_backend_load_model_interface():
    """バックエンドのload_modelインターフェーステスト
    
    Requirements: 12.2
    """
    # すべてのバックエンドがload_modelメソッドを持つことを確認
    backends = ["gemini", "openai", "local-cpu"]
    
    for backend in backends:
        llm_config = LLMConfig(backend=backend)
        llm_service = LLMService(llm_config)
        
        # load_modelメソッドが存在することを確認
        assert hasattr(llm_service, "load_model")
        assert callable(llm_service.load_model)
        
        embedding_config = EmbeddingConfig(backend=backend)
        embedding_service = EmbeddingService(embedding_config)
        
        # load_modelメソッドが存在することを確認
        assert hasattr(embedding_service, "load_model")
        assert callable(embedding_service.load_model)


def test_backend_is_loaded_interface():
    """バックエンドのis_loadedインターフェーステスト
    
    Requirements: 12.2
    """
    # すべてのバックエンドがis_loadedメソッドを持つことを確認
    backends = ["gemini", "openai", "local-cpu"]
    
    for backend in backends:
        llm_config = LLMConfig(backend=backend)
        llm_service = LLMService(llm_config)
        
        # is_loadedメソッドが存在し、初期状態ではFalseを返すことを確認
        assert hasattr(llm_service, "is_loaded")
        assert callable(llm_service.is_loaded)
        assert not llm_service.is_loaded()
        
        embedding_config = EmbeddingConfig(backend=backend)
        embedding_service = EmbeddingService(embedding_config)
        
        # is_loadedメソッドが存在し、初期状態ではFalseを返すことを確認
        assert hasattr(embedding_service, "is_loaded")
        assert callable(embedding_service.is_loaded)
        assert not embedding_service.is_loaded()
