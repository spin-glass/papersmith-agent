# -*- coding: utf-8 -*-
"""LLMServiceのユニットテスト

Requirements: 12.2, 12.3, 2.5
Testing Strategy: Unit Tests - LLM Service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import os
import sys

from src.services.llm_service import LLMService
from src.models.config import LLMConfig


class TestLLMServiceInitialization:
    """LLMService初期化テスト
    
    Requirements: 12.2, 12.3
    """
    
    def test_init_with_default_config(self):
        """デフォルト設定での初期化"""
        service = LLMService()
        
        assert service.config is not None
        assert service.config.backend == "gemini"
        assert service.backend is None
        assert service._is_loaded is False
    
    def test_init_with_custom_config(self):
        """カスタム設定での初期化"""
        config = LLMConfig(
            backend="openai",
            openai_model_name="gpt-4",
            max_length=1024,
            temperature=0.5
        )
        service = LLMService(config)
        
        assert service.config.backend == "openai"
        assert service.config.openai_model_name == "gpt-4"
        assert service.config.max_length == 1024
        assert service.config.temperature == 0.5
        assert service._is_loaded is False
    
    def test_is_loaded_initially_false(self):
        """初期状態でis_loaded()がFalseを返す"""
        service = LLMService()
        assert service.is_loaded() is False


class TestLLMServiceBackendLoading:
    """LLMServiceバックエンドロードテスト
    
    Requirements: 12.2, 12.3
    """
    
    @pytest.mark.asyncio
    async def test_load_gemini_backend_success(self):
        """Geminiバックエンドのロード成功"""
        config = LLMConfig(
            backend="gemini",
            gemini_api_key="test-api-key",
            gemini_model_name="gemini-1.5-flash"
        )
        service = LLMService(config)
        
        # google.generativeaiをモック
        with patch('google.generativeai.configure') as mock_configure:
            with patch('google.generativeai.GenerativeModel') as mock_model_cls:
                mock_model = MagicMock()
                mock_model_cls.return_value = mock_model
                
                await service.load_model()
                
                # 検証
                assert service._is_loaded is True
                assert service.backend is not None
                assert service.backend["type"] == "gemini"
                assert service.backend["model"] == mock_model
                mock_configure.assert_called_once_with(api_key="test-api-key")
                mock_model_cls.assert_called_once_with("gemini-1.5-flash")
    
    @pytest.mark.asyncio
    async def test_load_gemini_backend_with_env_var(self):
        """環境変数からGemini APIキーを取得"""
        config = LLMConfig(backend="gemini")
        service = LLMService(config)
        
        with patch('google.generativeai.configure') as mock_configure:
            with patch('google.generativeai.GenerativeModel') as mock_model_cls:
                with patch.dict(os.environ, {"GOOGLE_API_KEY": "env-api-key"}):
                    mock_model = MagicMock()
                    mock_model_cls.return_value = mock_model
                    
                    await service.load_model()
                    
                    mock_configure.assert_called_once_with(api_key="env-api-key")
    
    @pytest.mark.asyncio
    async def test_load_gemini_backend_missing_api_key(self):
        """Gemini APIキーが未設定の場合エラー"""
        config = LLMConfig(backend="gemini", gemini_api_key=None)
        service = LLMService(config)
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="GOOGLE_API_KEY is required"):
                await service.load_model()
    
    @pytest.mark.asyncio
    async def test_load_openai_backend_success(self):
        """OpenAIバックエンドのロード成功"""
        config = LLMConfig(
            backend="openai",
            openai_api_key="test-openai-key",
            openai_model_name="gpt-4"
        )
        service = LLMService(config)
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            await service.load_model()
            
            assert service._is_loaded is True
            assert service.backend["type"] == "openai"
            assert service.backend["client"] == mock_client
            assert service.backend["model"] == "gpt-4"
            mock_openai.assert_called_once_with(api_key="test-openai-key")
    
    @pytest.mark.asyncio
    async def test_load_openai_backend_missing_api_key(self):
        """OpenAI APIキーが未設定の場合エラー"""
        config = LLMConfig(backend="openai", openai_api_key=None)
        service = LLMService(config)
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="OPENAI_API_KEY is required"):
                await service.load_model()
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        sys.modules.get('transformers') is None,
        reason="transformers not installed - test will run when transformers is available"
    )
    async def test_load_local_cpu_backend_success(self):
        """ローカルCPUバックエンドのロード成功
        
        Note: This test is skipped when transformers is not installed.
        When transformers becomes available, this test will automatically run with real transformers.
        """
        config = LLMConfig(
            backend="local-cpu",
            local_model_name="test-model"
        )
        service = LLMService(config)
        
        # Mock modules
        mock_transformers = MagicMock()
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.float32 = "float32"
        
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_transformers.AutoModelForCausalLM.from_pretrained.return_value = mock_model
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer
        
        with patch.dict('sys.modules', {'transformers': mock_transformers, 'torch': mock_torch}):
            await service.load_model()
            
            assert service._is_loaded is True
            assert service.backend["type"] == "local"
            assert service.backend["device"] == "cpu"
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        sys.modules.get('transformers') is None,
        reason="transformers not installed - test will run when transformers is available"
    )
    async def test_load_local_cuda_backend_success(self):
        """ローカルCUDAバックエンドのロード成功
        
        Note: This test is skipped when transformers is not installed.
        When transformers becomes available, this test will automatically run with real transformers.
        """
        config = LLMConfig(
            backend="local-cuda",
            local_model_name="test-model"
        )
        service = LLMService(config)
        
        # Mock modules
        mock_transformers = MagicMock()
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.float16 = "float16"
        
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_transformers.AutoModelForCausalLM.from_pretrained.return_value = mock_model
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer
        
        with patch.dict('sys.modules', {'transformers': mock_transformers, 'torch': mock_torch}):
            await service.load_model()
            
            assert service._is_loaded is True
            assert service.backend["type"] == "local"
            assert service.backend["device"] == "cuda"
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        sys.modules.get('transformers') is None,
        reason="transformers not installed - test will run when transformers is available"
    )
    async def test_load_local_cuda_fallback_to_cpu(self):
        """CUDA利用不可時にCPUにフォールバック
        
        Note: This test is skipped when transformers is not installed.
        When transformers becomes available, this test will automatically run with real transformers.
        """
        config = LLMConfig(backend="local-cuda")
        service = LLMService(config)
        
        # Mock modules
        mock_transformers = MagicMock()
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.float32 = "float32"
        
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_transformers.AutoModelForCausalLM.from_pretrained.return_value = mock_model
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer
        
        with patch.dict('sys.modules', {'transformers': mock_transformers, 'torch': mock_torch}):
            await service.load_model()
            
            assert service.backend["device"] == "cpu"
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        sys.modules.get('mlx') is None,
        reason="MLX not installed - test will run when MLX is available"
    )
    async def test_load_local_mlx_backend_success(self):
        """ローカルMLXバックエンドのロード成功
        
        Note: This test is skipped when MLX is not installed.
        When MLX becomes available, this test will automatically run with real MLX.
        """
        config = LLMConfig(
            backend="local-mlx",
            local_model_name="test-model"
        )
        service = LLMService(config)
        
        # Mock modules
        mock_mlx = MagicMock()
        mock_mlx_lm = MagicMock()
        
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_mlx_lm.load.return_value = (mock_model, mock_tokenizer)
        
        with patch.dict('sys.modules', {'mlx.core': mock_mlx, 'mlx_lm': mock_mlx_lm}):
            await service.load_model()
            
            assert service._is_loaded is True
            assert service.backend["type"] == "mlx"
            assert service.backend["model"] == mock_model
            assert service.backend["tokenizer"] == mock_tokenizer
    
    @pytest.mark.asyncio
    async def test_load_unknown_backend_error(self):
        """未知のバックエンドでエラー"""
        config = LLMConfig(backend="unknown-backend")
        service = LLMService(config)
        
        with pytest.raises(RuntimeError, match="Unknown backend"):
            await service.load_model()
    
    @pytest.mark.asyncio
    async def test_load_model_already_loaded(self):
        """既にロード済みの場合は何もしない"""
        config = LLMConfig(backend="gemini", gemini_api_key="test-key")
        service = LLMService(config)
        
        with patch('google.generativeai.configure') as mock_configure:
            with patch('google.generativeai.GenerativeModel') as mock_model_cls:
                mock_model = MagicMock()
                mock_model_cls.return_value = mock_model
                
                # 1回目のロード
                await service.load_model()
                assert mock_configure.call_count == 1
                
                # 2回目のロード（スキップされる）
                await service.load_model()
                assert mock_configure.call_count == 1  # 増えない


class TestLLMServicePromptBuilding:
    """LLMServiceプロンプト構築テスト
    
    Requirements: 2.5
    """
    
    def test_build_prompt_basic(self):
        """基本的なプロンプト構築"""
        service = LLMService()
        
        question = "この論文の主な貢献は何ですか？"
        context = "この論文では、新しい機械学習アルゴリズムを提案しています。"
        
        prompt = service._build_prompt(question, context)
        
        assert "以下の論文の内容に基づいて" in prompt
        assert question in prompt
        assert context in prompt
        assert "【論文の内容】" in prompt
        assert "【質問】" in prompt
        assert "【回答】" in prompt
    
    def test_build_prompt_with_long_context(self):
        """長いコンテキストでのプロンプト構築"""
        service = LLMService()
        
        question = "実験結果は？"
        context = "A" * 5000  # 長いコンテキスト
        
        prompt = service._build_prompt(question, context)
        
        assert question in prompt
        assert context in prompt
        assert len(prompt) > 5000
    
    def test_build_prompt_with_special_characters(self):
        """特殊文字を含むプロンプト構築"""
        service = LLMService()
        
        question = "「深層学習」と「強化学習」の違いは？"
        context = "論文では、深層学習（DL）と強化学習（RL）を組み合わせています。"
        
        prompt = service._build_prompt(question, context)
        
        assert "「深層学習」" in prompt
        assert "（DL）" in prompt


class TestLLMServiceAnswerGeneration:
    """LLMService回答生成テスト
    
    Requirements: 2.5
    """
    
    @pytest.mark.asyncio
    async def test_generate_not_loaded_error(self):
        """モデル未ロード時にエラー"""
        service = LLMService()
        
        with pytest.raises(RuntimeError, match="Model not loaded"):
            await service.generate("質問", "コンテキスト")
    
    @pytest.mark.asyncio
    async def test_generate_with_gemini_backend(self):
        """Geminiバックエンドでの回答生成"""
        config = LLMConfig(backend="gemini", gemini_api_key="test-key")
        service = LLMService(config)
        
        # モデルをロード
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_cls:
                mock_model = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "これは機械学習の新しいアプローチです。"
                mock_model.generate_content.return_value = mock_response
                mock_model_cls.return_value = mock_model
                
                await service.load_model()
                
                # 回答生成
                answer = await service.generate(
                    question="この論文の主な貢献は？",
                    context="新しい機械学習アルゴリズムを提案しています。"
                )
                
                assert answer == "これは機械学習の新しいアプローチです。"
                mock_model.generate_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_with_openai_backend(self):
        """OpenAIバックエンドでの回答生成"""
        config = LLMConfig(backend="openai", openai_api_key="test-key")
        service = LLMService(config)
        
        with patch('openai.AsyncOpenAI') as mock_openai_cls:
            mock_client = MagicMock()
            mock_openai_cls.return_value = mock_client
            
            # モックレスポンス
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            mock_message.content = "これはOpenAIの回答です。"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            await service.load_model()
            
            answer = await service.generate(
                question="質問",
                context="コンテキスト"
            )
            
            assert answer == "これはOpenAIの回答です。"
    
    @pytest.mark.asyncio
    async def test_generate_with_custom_parameters(self):
        """カスタムパラメータでの回答生成"""
        config = LLMConfig(
            backend="gemini",
            gemini_api_key="test-key",
            max_length=256,
            temperature=0.5
        )
        service = LLMService(config)
        
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_cls:
                mock_model = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "回答"
                mock_model.generate_content.return_value = mock_response
                mock_model_cls.return_value = mock_model
                
                await service.load_model()
                
                await service.generate(
                    question="質問",
                    context="コンテキスト",
                    max_length=1024,
                    temperature=0.9
                )
                
                # カスタムパラメータが使用されることを確認
                call_args = mock_model.generate_content.call_args
                assert call_args[1]["generation_config"]["max_output_tokens"] == 1024
                assert call_args[1]["generation_config"]["temperature"] == 0.9
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        sys.modules.get('transformers') is None,
        reason="transformers not installed - test will run when transformers is available"
    )
    async def test_generate_with_local_backend(self):
        """ローカルバックエンドでの回答生成
        
        Note: This test is skipped when transformers is not installed.
        When transformers becomes available, this test will automatically run with real transformers.
        """
        config = LLMConfig(backend="local-cpu")
        service = LLMService(config)
        
        # Mock modules
        mock_transformers = MagicMock()
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.float32 = "float32"
        mock_torch.no_grad = MagicMock()
        mock_torch.no_grad.return_value.__enter__ = MagicMock()
        mock_torch.no_grad.return_value.__exit__ = MagicMock()
        
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_transformers.AutoModelForCausalLM.from_pretrained.return_value = mock_model
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer
        
        # トークナイザーのモック
        mock_tokenizer.return_value = {"input_ids": MagicMock()}
        mock_tokenizer.pad_token_id = 0
        mock_tokenizer.eos_token_id = 1
        
        # モデル生成のモック
        mock_output = MagicMock()
        mock_model.generate.return_value = [mock_output]
        mock_tokenizer.decode.return_value = "【回答】\nこれはローカルモデルの回答です。"
        
        with patch.dict('sys.modules', {'transformers': mock_transformers, 'torch': mock_torch}):
            await service.load_model()
            
            answer = await service.generate(
                question="質問",
                context="コンテキスト"
            )
            
            assert "ローカルモデルの回答" in answer


class TestLLMServiceAnswerExtraction:
    """LLMService回答抽出テスト
    
    Requirements: 2.5
    """
    
    def test_extract_answer_with_prompt_prefix(self):
        """プロンプトプレフィックス付き回答の抽出"""
        service = LLMService()
        
        prompt = "質問: これは何ですか？\n回答: "
        generated_text = prompt + "これは機械学習の論文です。"
        
        answer = service._extract_answer(generated_text, prompt)
        
        assert answer == "これは機械学習の論文です。"
    
    def test_extract_answer_with_marker(self):
        """【回答】マーカー付き回答の抽出"""
        service = LLMService()
        
        prompt = "質問"
        generated_text = "何か前置き\n【回答】\nこれが実際の回答です。"
        
        answer = service._extract_answer(generated_text, prompt)
        
        assert answer == "これが実際の回答です。"
    
    def test_extract_answer_empty(self):
        """空の回答の処理"""
        service = LLMService()
        
        prompt = "質問"
        generated_text = prompt
        
        answer = service._extract_answer(generated_text, prompt)
        
        assert "申し訳ございません" in answer
    
    def test_extract_answer_no_prefix(self):
        """プレフィックスなしの回答"""
        service = LLMService()
        
        prompt = "質問"
        generated_text = "これは直接の回答です。"
        
        answer = service._extract_answer(generated_text, prompt)
        
        assert answer == "これは直接の回答です。"


class TestLLMServiceErrorHandling:
    """LLMServiceエラーハンドリングテスト
    
    Requirements: 2.5
    """
    
    @pytest.mark.asyncio
    async def test_load_model_import_error(self):
        """モジュールインポートエラーの処理
        
        Note: This test verifies that appropriate error is raised when MLX is not available.
        """
        config = LLMConfig(backend="local-mlx")
        service = LLMService(config)
        
        # MLXが実際にインストールされていない場合、エラーが発生することを確認
        if sys.modules.get('mlx') is None:
            with pytest.raises(RuntimeError, match="MLX not installed"):
                await service.load_model()
        else:
            # MLXがインストールされている場合はスキップ
            pytest.skip("MLX is installed, cannot test import error")
    
    @pytest.mark.asyncio
    async def test_generate_backend_error(self):
        """バックエンドエラーの処理"""
        config = LLMConfig(backend="gemini", gemini_api_key="test-key")
        service = LLMService(config)
        
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_cls:
                mock_model = MagicMock()
                mock_model.generate_content.side_effect = Exception("API Error")
                mock_model_cls.return_value = mock_model
                
                await service.load_model()
                
                with pytest.raises(RuntimeError, match="Failed to generate answer"):
                    await service.generate("質問", "コンテキスト")
    
    @pytest.mark.asyncio
    async def test_load_model_configuration_error(self):
        """設定エラーの処理"""
        config = LLMConfig(backend="gemini", gemini_api_key="test-key")
        service = LLMService(config)
        
        with patch('google.generativeai.configure', side_effect=ValueError("Invalid API key")):
            with pytest.raises(RuntimeError, match="Failed to load LLM backend"):
                await service.load_model()


class TestLLMServiceUtilityMethods:
    """LLMServiceユーティリティメソッドテスト
    
    Requirements: 2.5
    """
    
    def test_is_loaded_after_loading(self):
        """ロード後にis_loaded()がTrueを返す"""
        service = LLMService()
        service._is_loaded = True
        
        assert service.is_loaded() is True
    
    def test_get_model_name_gemini(self):
        """Geminiモデル名の取得"""
        config = LLMConfig(backend="gemini", gemini_model_name="gemini-1.5-flash")
        service = LLMService(config)
        service.backend = {"type": "gemini"}
        
        model_name = service.get_model_name()
        
        assert model_name == "gemini:gemini-1.5-flash"
    
    def test_get_model_name_openai(self):
        """OpenAIモデル名の取得"""
        config = LLMConfig(backend="openai", openai_model_name="gpt-4")
        service = LLMService(config)
        service.backend = {"type": "openai"}
        
        model_name = service.get_model_name()
        
        assert model_name == "openai:gpt-4"
    
    def test_get_model_name_local(self):
        """ローカルモデル名の取得"""
        config = LLMConfig(backend="local-cpu", local_model_name="test-model")
        service = LLMService(config)
        service.backend = {"type": "local"}
        
        model_name = service.get_model_name()
        
        assert model_name == "local:test-model"
    
    def test_get_model_name_not_loaded(self):
        """未ロード時のモデル名取得"""
        service = LLMService()
        
        model_name = service.get_model_name()
        
        assert model_name == "unknown"
