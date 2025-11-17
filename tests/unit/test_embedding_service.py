"""EmbeddingServiceのユニットテスト

Requirements: 12.2, 12.3, 2.2
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import numpy as np
import os

from src.services.embedding_service import EmbeddingService
from src.models.config import EmbeddingConfig


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def embedding_config_local_cpu():
    """ローカルCPUバックエンド設定"""
    return EmbeddingConfig(
        backend="local-cpu",
        local_model_name="intfloat/multilingual-e5-base",
        batch_size=2,
        normalize_embeddings=True
    )


@pytest.fixture
def embedding_config_gemini():
    """Geminiバックエンド設定"""
    return EmbeddingConfig(
        backend="gemini",
        gemini_api_key="test-api-key",
        batch_size=32
    )


@pytest.fixture
def embedding_config_openai():
    """OpenAIバックエンド設定"""
    return EmbeddingConfig(
        backend="openai",
        openai_api_key="test-api-key",
        openai_embedding_model="text-embedding-3-small",
        batch_size=32
    )


@pytest.fixture
def embedding_config_local_cuda():
    """ローカルCUDAバックエンド設定"""
    return EmbeddingConfig(
        backend="local-cuda",
        local_model_name="intfloat/multilingual-e5-base",
        batch_size=8
    )


@pytest.fixture
def embedding_config_local_mlx():
    """ローカルMLXバックエンド設定"""
    return EmbeddingConfig(
        backend="local-mlx",
        local_model_name="intfloat/multilingual-e5-base",
        batch_size=8
    )


# ============================================================================
# Backend Initialization Tests (全5バックエンド)
# Requirements: 12.2, 12.3
# ============================================================================

@pytest.mark.asyncio
async def test_init_default_config():
    """デフォルト設定で初期化"""
    service = EmbeddingService()
    
    assert service.config is not None
    assert service.config.backend == "gemini"  # デフォルトはgemini
    assert service.backend is None
    assert not service.is_loaded()


@pytest.mark.asyncio
async def test_init_with_custom_config(embedding_config_local_cpu):
    """カスタム設定で初期化"""
    service = EmbeddingService(config=embedding_config_local_cpu)
    
    assert service.config == embedding_config_local_cpu
    assert service.config.backend == "local-cpu"
    assert not service.is_loaded()


@pytest.mark.asyncio
async def test_load_gemini_backend(embedding_config_gemini):
    """Geminiバックエンドのロード"""
    service = EmbeddingService(config=embedding_config_gemini)
    
    # google.generativeaiをモック
    mock_genai = MagicMock()
    
    with patch.dict('sys.modules', {'google.generativeai': mock_genai}):
        with patch.object(service, '_load_gemini_backend', return_value={
            "type": "gemini",
            "client": mock_genai
        }):
            await service.load_model()
            
            assert service.is_loaded()
            assert service.backend["type"] == "gemini"


@pytest.mark.asyncio
async def test_load_gemini_backend_missing_api_key():
    """Geminiバックエンド: APIキー未設定時のエラー"""
    config = EmbeddingConfig(backend="gemini", gemini_api_key=None)
    service = EmbeddingService(config=config)
    
    # 環境変数もクリア
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError, match="Failed to load embedding backend"):
            await service.load_model()


@pytest.mark.asyncio
async def test_load_openai_backend(embedding_config_openai):
    """OpenAIバックエンドのロード"""
    service = EmbeddingService(config=embedding_config_openai)
    
    # openaiモジュールをモック
    mock_openai = MagicMock()
    mock_client = MagicMock()
    mock_openai.AsyncOpenAI.return_value = mock_client
    
    with patch.dict('sys.modules', {'openai': mock_openai}):
        with patch.object(service, '_load_openai_backend', return_value={
            "type": "openai",
            "client": mock_client,
            "model": "text-embedding-3-small"
        }):
            await service.load_model()
            
            assert service.is_loaded()
            assert service.backend["type"] == "openai"
            assert service.backend["model"] == "text-embedding-3-small"


@pytest.mark.asyncio
async def test_load_openai_backend_missing_api_key():
    """OpenAIバックエンド: APIキー未設定時のエラー"""
    config = EmbeddingConfig(backend="openai", openai_api_key=None)
    service = EmbeddingService(config=config)
    
    # 環境変数もクリア
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError, match="Failed to load embedding backend"):
            await service.load_model()


@pytest.mark.asyncio
async def test_load_local_cpu_backend(embedding_config_local_cpu):
    """ローカルCPUバックエンドのロード"""
    service = EmbeddingService(config=embedding_config_local_cpu)
    
    # sentence_transformersをモック
    mock_model = MagicMock()
    mock_model.get_sentence_embedding_dimension.return_value = 768
    
    mock_st = MagicMock()
    mock_st.SentenceTransformer.return_value = mock_model
    
    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = False
    
    # sys.modulesレベルでモック
    with patch.dict('sys.modules', {
        'sentence_transformers': mock_st,
        'torch': mock_torch
    }):
        await service.load_model()
        
        assert service.is_loaded()
        assert service.backend["type"] == "local"
        assert service.backend["device"] == "cpu"


@pytest.mark.asyncio
async def test_load_local_cuda_backend(embedding_config_local_cuda):
    """ローカルCUDAバックエンドのロード"""
    service = EmbeddingService(config=embedding_config_local_cuda)
    
    # sentence_transformersをモック
    mock_model = MagicMock()
    mock_model.get_sentence_embedding_dimension.return_value = 768
    
    mock_st = MagicMock()
    mock_st.SentenceTransformer.return_value = mock_model
    
    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = True
    
    # sys.modulesレベルでモック
    with patch.dict('sys.modules', {
        'sentence_transformers': mock_st,
        'torch': mock_torch
    }):
        await service.load_model()
        
        assert service.is_loaded()
        assert service.backend["type"] == "local"
        assert service.backend["device"] == "cuda"


@pytest.mark.asyncio
async def test_load_local_cuda_fallback_to_cpu(embedding_config_local_cuda):
    """ローカルCUDAバックエンド: CUDA利用不可時のCPUフォールバック"""
    service = EmbeddingService(config=embedding_config_local_cuda)
    
    # sentence_transformersをモック
    mock_model = MagicMock()
    
    mock_st = MagicMock()
    mock_st.SentenceTransformer.return_value = mock_model
    
    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = False
    
    # sys.modulesレベルでモック
    with patch.dict('sys.modules', {
        'sentence_transformers': mock_st,
        'torch': mock_torch
    }):
        await service.load_model()
        
        assert service.is_loaded()
        assert service.backend["device"] == "cpu"  # CPUにフォールバック


@pytest.mark.asyncio
async def test_load_local_mlx_backend_not_implemented(embedding_config_local_mlx):
    """ローカルMLXバックエンド: 未実装エラー"""
    service = EmbeddingService(config=embedding_config_local_mlx)
    
    # mlx.coreをモック（インポート成功させる）
    mock_mlx = MagicMock()
    
    with patch.dict('sys.modules', {'mlx': MagicMock(), 'mlx.core': mock_mlx}):
        with pytest.raises(RuntimeError, match="not yet implemented|Failed to load embedding backend"):
            await service.load_model()


@pytest.mark.asyncio
async def test_load_local_mlx_backend_missing_dependency(embedding_config_local_mlx):
    """ローカルMLXバックエンド: 依存関係未インストール時のエラー"""
    service = EmbeddingService(config=embedding_config_local_mlx)
    
    # mlx.coreのインポートエラーをシミュレート
    with patch.dict('sys.modules', {'mlx.core': None}):
        with patch('src.services.embedding_service.EmbeddingService._load_local_backend', 
                   side_effect=RuntimeError("MLX not installed")):
            with pytest.raises(RuntimeError, match="Failed to load embedding backend"):
                await service.load_model()


@pytest.mark.asyncio
async def test_load_unknown_backend():
    """未知のバックエンド指定時のエラー"""
    config = EmbeddingConfig(backend="unknown-backend")
    service = EmbeddingService(config=config)
    
    with pytest.raises(RuntimeError, match="Unknown backend"):
        await service.load_model()


@pytest.mark.asyncio
async def test_load_model_already_loaded(embedding_config_local_cpu):
    """既にロード済みの場合は何もしない"""
    service = EmbeddingService(config=embedding_config_local_cpu)
    
    # 最初のロード
    mock_backend = {"type": "local", "model": Mock(), "device": "cpu"}
    with patch.object(service, '_load_local_backend', return_value=mock_backend) as mock_load:
        await service.load_model()
        assert mock_load.call_count == 1
        
        # 2回目のロード（スキップされる）
        await service.load_model()
        assert mock_load.call_count == 1  # 呼ばれない


# ============================================================================
# Single Text Embedding Tests
# Requirements: 2.2
# ============================================================================

@pytest.mark.asyncio
async def test_embed_single_text_local_backend():
    """ローカルバックエンド: 単一テキストのEmbedding生成"""
    config = EmbeddingConfig(backend="local-cpu")
    service = EmbeddingService(config=config)
    
    # モックモデルの設定
    mock_model = Mock()
    mock_embedding = np.array([0.1, 0.2, 0.3])
    mock_model.encode.return_value = mock_embedding
    
    # backendを直接設定
    service.backend = {"type": "local", "model": mock_model, "device": "cpu"}
    service._is_loaded = True
    
    result = await service.embed("test text")
    
    assert isinstance(result, list)
    assert len(result) == 3
    assert result == [0.1, 0.2, 0.3]
    mock_model.encode.assert_called_once()


@pytest.mark.asyncio
async def test_embed_single_text_gemini_backend():
    """Geminiバックエンド: 単一テキストのEmbedding生成"""
    config = EmbeddingConfig(backend="gemini")
    service = EmbeddingService(config=config)
    
    # モッククライアントの設定
    mock_client = MagicMock()
    mock_client.embed_content.return_value = {'embedding': [0.1, 0.2, 0.3]}
    
    service.backend = {"type": "gemini", "client": mock_client}
    service._is_loaded = True
    
    result = await service.embed("test text")
    
    assert isinstance(result, list)
    assert len(result) == 3
    assert result == [0.1, 0.2, 0.3]
    mock_client.embed_content.assert_called_once_with(
        model="models/text-embedding-004",
        content="test text",
        task_type="retrieval_document"
    )


@pytest.mark.asyncio
async def test_embed_single_text_openai_backend():
    """OpenAIバックエンド: 単一テキストのEmbedding生成"""
    config = EmbeddingConfig(backend="openai")
    service = EmbeddingService(config=config)
    
    # モッククライアントの設定
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
    
    mock_client = AsyncMock()
    mock_client.embeddings.create.return_value = mock_response
    
    service.backend = {
        "type": "openai",
        "client": mock_client,
        "model": "text-embedding-3-small"
    }
    service._is_loaded = True
    
    result = await service.embed("test text")
    
    assert isinstance(result, list)
    assert len(result) == 3
    assert result == [0.1, 0.2, 0.3]
    mock_client.embeddings.create.assert_called_once()


@pytest.mark.asyncio
async def test_embed_without_loading_model():
    """モデル未ロード時のエラー"""
    config = EmbeddingConfig(backend="local-cpu")
    service = EmbeddingService(config=config)
    
    with pytest.raises(RuntimeError, match="Model not loaded"):
        await service.embed("test text")


@pytest.mark.asyncio
async def test_embed_with_backend_error():
    """Embedding生成時のバックエンドエラー"""
    config = EmbeddingConfig(backend="local-cpu")
    service = EmbeddingService(config=config)
    
    # エラーを発生させるモックモデル
    mock_model = Mock()
    mock_model.encode.side_effect = Exception("Backend error")
    
    service.backend = {"type": "local", "model": mock_model, "device": "cpu"}
    service._is_loaded = True
    
    with pytest.raises(RuntimeError, match="Failed to generate embedding"):
        await service.embed("test text")


# ============================================================================
# Batch Embedding Tests
# Requirements: 2.2
# ============================================================================

@pytest.mark.asyncio
async def test_embed_batch_local_backend():
    """ローカルバックエンド: バッチEmbedding生成"""
    config = EmbeddingConfig(backend="local-cpu", batch_size=2)
    service = EmbeddingService(config=config)
    
    # モックモデルの設定
    mock_model = Mock()
    mock_embeddings = np.array([[0.1, 0.2], [0.3, 0.4]])
    mock_model.encode.return_value = mock_embeddings
    
    service.backend = {"type": "local", "model": mock_model, "device": "cpu"}
    service._is_loaded = True
    
    results = await service.embed_batch(["text1", "text2"])
    
    assert isinstance(results, list)
    assert len(results) == 2
    assert results[0] == [0.1, 0.2]
    assert results[1] == [0.3, 0.4]
    mock_model.encode.assert_called_once()


@pytest.mark.asyncio
async def test_embed_batch_gemini_backend():
    """Geminiバックエンド: バッチEmbedding生成（逐次処理）"""
    config = EmbeddingConfig(backend="gemini")
    service = EmbeddingService(config=config)
    
    # モッククライアントの設定
    mock_client = MagicMock()
    mock_client.embed_content.side_effect = [
        {'embedding': [0.1, 0.2]},
        {'embedding': [0.3, 0.4]}
    ]
    
    service.backend = {"type": "gemini", "client": mock_client}
    service._is_loaded = True
    
    results = await service.embed_batch(["text1", "text2"])
    
    assert isinstance(results, list)
    assert len(results) == 2
    assert results[0] == [0.1, 0.2]
    assert results[1] == [0.3, 0.4]
    assert mock_client.embed_content.call_count == 2


@pytest.mark.asyncio
async def test_embed_batch_openai_backend():
    """OpenAIバックエンド: バッチEmbedding生成"""
    config = EmbeddingConfig(backend="openai")
    service = EmbeddingService(config=config)
    
    # モッククライアントの設定
    mock_response = MagicMock()
    mock_response.data = [
        MagicMock(embedding=[0.1, 0.2]),
        MagicMock(embedding=[0.3, 0.4])
    ]
    
    mock_client = AsyncMock()
    mock_client.embeddings.create.return_value = mock_response
    
    service.backend = {
        "type": "openai",
        "client": mock_client,
        "model": "text-embedding-3-small"
    }
    service._is_loaded = True
    
    results = await service.embed_batch(["text1", "text2"])
    
    assert isinstance(results, list)
    assert len(results) == 2
    assert results[0] == [0.1, 0.2]
    assert results[1] == [0.3, 0.4]


@pytest.mark.asyncio
async def test_embed_batch_empty_list():
    """空リストのバッチ処理"""
    config = EmbeddingConfig(backend="local-cpu")
    service = EmbeddingService(config=config)
    
    mock_model = Mock()
    service.backend = {"type": "local", "model": mock_model, "device": "cpu"}
    service._is_loaded = True
    
    results = await service.embed_batch([])
    
    assert results == []
    mock_model.encode.assert_not_called()


@pytest.mark.asyncio
async def test_embed_batch_without_loading_model():
    """モデル未ロード時のエラー"""
    config = EmbeddingConfig(backend="local-cpu")
    service = EmbeddingService(config=config)
    
    with pytest.raises(RuntimeError, match="Model not loaded"):
        await service.embed_batch(["text1", "text2"])


@pytest.mark.asyncio
async def test_embed_batch_with_backend_error():
    """バッチEmbedding生成時のバックエンドエラー"""
    config = EmbeddingConfig(backend="local-cpu")
    service = EmbeddingService(config=config)
    
    # エラーを発生させるモックモデル
    mock_model = Mock()
    mock_model.encode.side_effect = Exception("Backend error")
    
    service.backend = {"type": "local", "model": mock_model, "device": "cpu"}
    service._is_loaded = True
    
    with pytest.raises(RuntimeError, match="Failed to generate batch embeddings"):
        await service.embed_batch(["text1", "text2"])


# ============================================================================
# Utility Methods Tests
# ============================================================================

@pytest.mark.asyncio
async def test_is_loaded():
    """is_loaded()メソッドのテスト"""
    config = EmbeddingConfig(backend="local-cpu")
    service = EmbeddingService(config=config)
    
    assert not service.is_loaded()
    
    # ロード後
    service._is_loaded = True
    assert service.is_loaded()


@pytest.mark.asyncio
async def test_get_embedding_dimension_not_loaded():
    """モデル未ロード時のget_embedding_dimension()"""
    config = EmbeddingConfig(backend="local-cpu")
    service = EmbeddingService(config=config)
    
    assert service.get_embedding_dimension() is None


@pytest.mark.asyncio
async def test_get_embedding_dimension_gemini():
    """Geminiバックエンドのembedding次元数"""
    config = EmbeddingConfig(backend="gemini")
    service = EmbeddingService(config=config)
    
    service.backend = {"type": "gemini", "client": MagicMock()}
    service._is_loaded = True
    
    assert service.get_embedding_dimension() == 768


@pytest.mark.asyncio
async def test_get_embedding_dimension_openai_small():
    """OpenAIバックエンド（small）のembedding次元数"""
    config = EmbeddingConfig(backend="openai")
    service = EmbeddingService(config=config)
    
    service.backend = {
        "type": "openai",
        "client": AsyncMock(),
        "model": "text-embedding-3-small"
    }
    service._is_loaded = True
    
    assert service.get_embedding_dimension() == 1536


@pytest.mark.asyncio
async def test_get_embedding_dimension_openai_large():
    """OpenAIバックエンド（large）のembedding次元数"""
    config = EmbeddingConfig(backend="openai")
    service = EmbeddingService(config=config)
    
    service.backend = {
        "type": "openai",
        "client": AsyncMock(),
        "model": "text-embedding-3-large"
    }
    service._is_loaded = True
    
    assert service.get_embedding_dimension() == 3072


@pytest.mark.asyncio
async def test_get_embedding_dimension_local():
    """ローカルバックエンドのembedding次元数"""
    config = EmbeddingConfig(backend="local-cpu")
    service = EmbeddingService(config=config)
    
    mock_model = MagicMock()
    mock_model.get_sentence_embedding_dimension.return_value = 768
    
    service.backend = {"type": "local", "model": mock_model, "device": "cpu"}
    service._is_loaded = True
    
    assert service.get_embedding_dimension() == 768
    mock_model.get_sentence_embedding_dimension.assert_called_once()


# ============================================================================
# Error Handling Tests
# Requirements: 12.2, 12.3
# ============================================================================

@pytest.mark.asyncio
async def test_embed_unknown_backend_type():
    """未知のバックエンドタイプでのembedding生成エラー"""
    config = EmbeddingConfig(backend="local-cpu")
    service = EmbeddingService(config=config)
    
    # 未知のバックエンドタイプを設定
    service.backend = {"type": "unknown"}
    service._is_loaded = True
    
    with pytest.raises(RuntimeError, match="Failed to generate embedding"):
        await service.embed("test text")


@pytest.mark.asyncio
async def test_embed_batch_unknown_backend_type():
    """未知のバックエンドタイプでのバッチembedding生成エラー"""
    config = EmbeddingConfig(backend="local-cpu")
    service = EmbeddingService(config=config)
    
    # 未知のバックエンドタイプを設定
    service.backend = {"type": "unknown"}
    service._is_loaded = True
    
    with pytest.raises(RuntimeError, match="Failed to generate batch embeddings"):
        await service.embed_batch(["text1", "text2"])


# ============================================================================
# Additional Coverage Tests
# ============================================================================

@pytest.mark.asyncio
async def test_load_gemini_backend_with_env_var():
    """Geminiバックエンド: 環境変数からAPIキー取得"""
    config = EmbeddingConfig(backend="gemini", gemini_api_key=None)
    service = EmbeddingService(config=config)
    
    mock_genai = MagicMock()
    
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "env-api-key"}):
        with patch.dict('sys.modules', {'google.generativeai': mock_genai, 'google': MagicMock()}):
            with patch.object(service, '_load_gemini_backend', return_value={
                "type": "gemini",
                "client": mock_genai
            }):
                await service.load_model()
                
                assert service.is_loaded()


@pytest.mark.asyncio
async def test_load_openai_backend_with_env_var():
    """OpenAIバックエンド: 環境変数からAPIキー取得"""
    config = EmbeddingConfig(backend="openai", openai_api_key=None)
    service = EmbeddingService(config=config)
    
    mock_openai = MagicMock()
    mock_client = MagicMock()
    mock_openai.AsyncOpenAI.return_value = mock_client
    
    with patch.dict(os.environ, {"OPENAI_API_KEY": "env-api-key"}):
        with patch.dict('sys.modules', {'openai': mock_openai}):
            with patch.object(service, '_load_openai_backend', return_value={
                "type": "openai",
                "client": mock_client,
                "model": "text-embedding-3-small"
            }):
                await service.load_model()
                
                assert service.is_loaded()


@pytest.mark.asyncio
async def test_load_local_backend_missing_dependencies():
    """ローカルバックエンド: 依存関係未インストール時のエラー"""
    config = EmbeddingConfig(backend="local-cpu")
    service = EmbeddingService(config=config)
    
    # sentence_transformersのインポートエラーをシミュレート
    def mock_import(name, *args, **kwargs):
        if name == 'sentence_transformers':
            raise ImportError("No module named 'sentence_transformers'")
        return MagicMock()
    
    with patch('builtins.__import__', side_effect=mock_import):
        with pytest.raises(RuntimeError, match="Failed to load embedding backend"):
            await service.load_model()


@pytest.mark.asyncio
async def test_get_embedding_dimension_unknown_backend():
    """未知のバックエンドタイプのembedding次元数"""
    config = EmbeddingConfig(backend="local-cpu")
    service = EmbeddingService(config=config)
    
    # 未知のバックエンドタイプを設定
    service.backend = {"type": "unknown"}
    service._is_loaded = True
    
    # 未知のバックエンドの場合はNoneを返す
    assert service.get_embedding_dimension() is None


@pytest.mark.asyncio
async def test_get_embedding_dimension_openai_default():
    """OpenAIバックエンド（デフォルトモデル）のembedding次元数"""
    config = EmbeddingConfig(backend="openai")
    service = EmbeddingService(config=config)
    
    service.backend = {
        "type": "openai",
        "client": AsyncMock(),
        "model": "text-embedding-ada-002"  # デフォルトケース
    }
    service._is_loaded = True
    
    assert service.get_embedding_dimension() == 1536
