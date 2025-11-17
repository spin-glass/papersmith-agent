# -*- coding: utf-8 -*-
"""LLM推論サービス（マルチバックエンド対応）

Requirements: 2.5
"""

from typing import Optional
import logging
import os

from src.models.config import LLMConfig


logger = logging.getLogger(__name__)


class LLMService:
    """LLM推論サービス（マルチバックエンド対応）
    
    複数のバックエンドをサポート:
    - gemini: Google Gemini API
    - openai: OpenAI API
    - local-cpu: ローカルCPU (transformers)
    - local-mlx: Mac GPU (MLX)
    - local-cuda: NVIDIA GPU (CUDA)
    
    Requirements: 2.5
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """初期化
        
        Args:
            config: LLM設定（Noneの場合はデフォルト設定を使用）
        """
        self.config = config or LLMConfig()
        self.backend = None
        self._is_loaded = False
        
        logger.info(
            f"LLMService initialized with backend: {self.config.backend}"
        )
    
    async def load_model(self) -> None:
        """モデルをロード
        
        バックエンドに応じて適切なモデルをロードします。
        既にロード済みの場合は何もしません。
        
        Requirements: 2.5
        """
        if self._is_loaded:
            logger.info("Model already loaded, skipping")
            return
        
        try:
            backend_type = self.config.backend
            logger.info(f"Loading LLM backend: {backend_type}")
            
            if backend_type == "gemini":
                self.backend = await self._load_gemini_backend()
            elif backend_type == "openai":
                self.backend = await self._load_openai_backend()
            elif backend_type.startswith("local-"):
                self.backend = await self._load_local_backend(backend_type)
            else:
                raise ValueError(f"Unknown backend: {backend_type}")
            
            self._is_loaded = True
            logger.info(f"Successfully loaded LLM backend: {backend_type}")
            
        except Exception as e:
            logger.error(f"Failed to load LLM backend: {e}")
            raise RuntimeError(f"Failed to load LLM backend: {e}") from e
    
    async def _load_gemini_backend(self):
        """Geminiバックエンドをロード"""
        import google.generativeai as genai
        
        api_key = self.config.gemini_api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is required for gemini backend")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(self.config.gemini_model_name)
        
        logger.info(f"Gemini backend configured with model: {self.config.gemini_model_name}")
        return {"type": "gemini", "model": model}
    
    async def _load_openai_backend(self):
        """OpenAIバックエンドをロード"""
        from openai import AsyncOpenAI
        
        api_key = self.config.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for openai backend")
        
        client = AsyncOpenAI(api_key=api_key)
        logger.info(f"OpenAI backend configured with model: {self.config.openai_model_name}")
        return {
            "type": "openai",
            "client": client,
            "model": self.config.openai_model_name
        }
    
    async def _load_local_backend(self, backend_type: str):
        """ローカルバックエンドをロード"""
        if backend_type == "local-mlx":
            # MLX backend (Mac GPU)
            try:
                import mlx.core as mx
                from mlx_lm import load, generate
                
                logger.info("Loading MLX model...")
                model, tokenizer = load(self.config.local_model_name)
                
                logger.info("MLX backend loaded")
                return {
                    "type": "mlx",
                    "model": model,
                    "tokenizer": tokenizer,
                    "generate_fn": generate
                }
            except ImportError:
                raise RuntimeError(
                    "MLX not installed. Install with: pip install mlx mlx-lm"
                )
        
        elif backend_type in ["local-cpu", "local-cuda"]:
            # transformers backend
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer
                import torch
                
                device = "cpu" if backend_type == "local-cpu" else "cuda"
                
                if device == "cuda" and not torch.cuda.is_available():
                    logger.warning("CUDA not available, falling back to CPU")
                    device = "cpu"
                
                logger.info(f"Loading tokenizer: {self.config.local_model_name}")
                tokenizer = AutoTokenizer.from_pretrained(self.config.local_model_name)
                
                logger.info(f"Loading model: {self.config.local_model_name}")
                torch_dtype = torch.float16 if device == "cuda" else torch.float32
                model = AutoModelForCausalLM.from_pretrained(
                    self.config.local_model_name,
                    torch_dtype=torch_dtype,
                    device_map="auto" if device == "cuda" else None
                )
                
                if device == "cpu":
                    model = model.to(device)
                
                logger.info(f"Local model loaded on {device}")
                return {
                    "type": "local",
                    "model": model,
                    "tokenizer": tokenizer,
                    "device": device
                }
            except ImportError:
                raise RuntimeError(
                    "transformers not installed. "
                    "Install with: pip install transformers torch"
                )
        
        raise ValueError(f"Unknown local backend: {backend_type}")

    async def generate(
        self,
        question: str,
        context: str,
        max_length: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """回答生成
        
        質問とコンテキストからプロンプトを構築し、LLMで回答を生成します。
        
        Args:
            question: ユーザーの質問
            context: RAGで取得した論文のコンテキスト
            max_length: 最大生成トークン数（Noneの場合は設定値を使用）
            temperature: 生成温度（Noneの場合は設定値を使用）
            
        Returns:
            生成された回答テキスト
            
        Raises:
            RuntimeError: モデルが未ロードの場合
            
        Requirements: 2.5
        """
        if not self._is_loaded or self.backend is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            # プロンプト構築
            prompt = self._build_prompt(question, context)
            
            # パラメータ設定
            max_len = max_length or self.config.max_length
            temp = temperature or self.config.temperature
            
            logger.info(
                f"Generating answer with max_length={max_len}, temperature={temp}"
            )
            
            backend_type = self.backend["type"]
            
            if backend_type == "gemini":
                response = self.backend["model"].generate_content(
                    prompt,
                    generation_config={
                        "max_output_tokens": max_len,
                        "temperature": temp,
                    }
                )
                answer = response.text
            
            elif backend_type == "openai":
                response = await self.backend["client"].chat.completions.create(
                    model=self.backend["model"],
                    messages=[
                        {"role": "system", "content": "あなたは論文解析の専門家です。提供された論文の内容に基づいて、正確に質問に答えてください。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_len,
                    temperature=temp
                )
                answer = response.choices[0].message.content
            
            elif backend_type == "mlx":
                # MLX generation
                response = self.backend["generate_fn"](
                    self.backend["model"],
                    self.backend["tokenizer"],
                    prompt=prompt,
                    max_tokens=max_len,
                    temp=temp
                )
                answer = response
            
            elif backend_type == "local":
                # transformers generation
                import torch
                
                tokenizer = self.backend["tokenizer"]
                model = self.backend["model"]
                device = self.backend["device"]
                
                inputs = tokenizer(
                    prompt,
                    return_tensors="pt",
                    truncation=True,
                    max_length=2048
                )
                
                if device == "cuda":
                    inputs = {k: v.to(device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=max_len,
                        temperature=temp,
                        do_sample=True,
                        top_p=0.9,
                        pad_token_id=tokenizer.pad_token_id,
                        eos_token_id=tokenizer.eos_token_id
                    )
                
                generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
                answer = self._extract_answer(generated_text, prompt)
            
            else:
                raise ValueError(f"Unknown backend type: {backend_type}")
            
            logger.info(f"Successfully generated answer (length: {len(answer)})")
            return answer
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            raise RuntimeError(f"Failed to generate answer: {e}") from e
    
    def _build_prompt(self, question: str, context: str) -> str:
        """プロンプト構築
        
        日本語プロンプトテンプレートを使用して、
        質問とコンテキストからプロンプトを構築します。
        
        Args:
            question: ユーザーの質問
            context: 論文のコンテキスト
            
        Returns:
            構築されたプロンプト
            
        Requirements: 2.5
        """
        prompt = f"""以下の論文の内容に基づいて、質問に日本語で回答してください。

【論文の内容】
{context}

【質問】
{question}

【回答】
"""
        return prompt
    
    def _extract_answer(self, generated_text: str, prompt: str) -> str:
        """生成テキストから回答部分を抽出
        
        生成されたテキストからプロンプト部分を除去し、
        回答部分のみを抽出します。
        
        Args:
            generated_text: LLMが生成した全テキスト
            prompt: 使用したプロンプト
            
        Returns:
            抽出された回答テキスト
            
        Requirements: 2.5
        """
        # プロンプト部分を除去
        if generated_text.startswith(prompt):
            answer = generated_text[len(prompt):].strip()
        else:
            answer = generated_text.strip()
        
        # 【回答】マーカー以降を抽出（存在する場合）
        if "【回答】" in answer:
            answer = answer.split("【回答】", 1)[1].strip()
        
        # 空の回答の場合はデフォルトメッセージ
        if not answer:
            answer = "申し訳ございません。回答を生成できませんでした。"
        
        return answer
    
    def is_loaded(self) -> bool:
        """モデルがロード済みかどうかを返す
        
        Returns:
            ロード済みの場合True
        """
        return self._is_loaded
    
    def get_model_name(self) -> str:
        """使用中のモデル名を返す
        
        Returns:
            モデル名
        """
        backend_type = self.backend["type"] if self.backend else "unknown"
        
        if backend_type == "gemini":
            return f"gemini:{self.config.gemini_model_name}"
        elif backend_type == "openai":
            return f"openai:{self.config.openai_model_name}"
        elif backend_type in ["local", "mlx"]:
            return f"local:{self.config.local_model_name}"
        
        return "unknown"
