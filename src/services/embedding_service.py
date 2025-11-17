# -*- coding: utf-8 -*-
"""Embedding生成サービス（マルチバックエンド対応）

Requirements: 2.2
"""

from typing import List, Optional
import logging
import os

from src.models.config import EmbeddingConfig


logger = logging.getLogger(__name__)


class EmbeddingService:
    """Embedding生成サービス（マルチバックエンド対応）
    
    複数のバックエンドをサポート:
    - gemini: Google Gemini API
    - openai: OpenAI API
    - local-cpu: ローカルCPU (sentence-transformers)
    - local-mlx: Mac GPU (MLX)
    - local-cuda: NVIDIA GPU (CUDA)
    
    Requirements: 2.2
    """
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """初期化
        
        Args:
            config: Embedding設定（Noneの場合はデフォルト設定を使用）
        """
        self.config = config or EmbeddingConfig()
        self.backend = None
        self._is_loaded = False
        
        logger.info(
            f"EmbeddingService initialized with backend: {self.config.backend}"
        )
    
    async def load_model(self) -> None:
        """モデルをロード
        
        バックエンドに応じて適切なモデルをロードします。
        既にロード済みの場合は何もしません。
        
        Requirements: 2.2
        """
        if self._is_loaded:
            logger.info("Model already loaded, skipping")
            return
        
        try:
            backend_type = self.config.backend
            logger.info(f"Loading embedding backend: {backend_type}")
            
            if backend_type == "gemini":
                self.backend = await self._load_gemini_backend()
            elif backend_type == "openai":
                self.backend = await self._load_openai_backend()
            elif backend_type.startswith("local-"):
                self.backend = await self._load_local_backend(backend_type)
            else:
                raise ValueError(f"Unknown backend: {backend_type}")
            
            self._is_loaded = True
            logger.info(f"Successfully loaded embedding backend: {backend_type}")
            
        except Exception as e:
            logger.error(f"Failed to load embedding backend: {e}")
            raise RuntimeError(f"Failed to load embedding backend: {e}") from e
    
    async def _load_gemini_backend(self):
        """Geminiバックエンドをロード"""
        import google.generativeai as genai
        
        api_key = self.config.gemini_api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is required for gemini backend")
        
        genai.configure(api_key=api_key)
        logger.info("Gemini backend configured")
        return {"type": "gemini", "client": genai}
    
    async def _load_openai_backend(self):
        """OpenAIバックエンドをロード"""
        from openai import AsyncOpenAI
        
        api_key = self.config.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for openai backend")
        
        client = AsyncOpenAI(api_key=api_key)
        logger.info("OpenAI backend configured")
        return {
            "type": "openai",
            "client": client,
            "model": self.config.openai_embedding_model
        }
    
    async def _load_local_backend(self, backend_type: str):
        """ローカルバックエンドをロード"""
        if backend_type == "local-mlx":
            # MLX backend (Mac GPU)
            try:
                import mlx.core as mx
                logger.info("MLX backend available")
                # TODO: MLX embedding implementation
                raise NotImplementedError("MLX embedding backend not yet implemented")
            except ImportError:
                raise RuntimeError(
                    "MLX not installed. Install with: pip install mlx mlx-lm"
                )
        
        elif backend_type in ["local-cpu", "local-cuda"]:
            # sentence-transformers backend
            try:
                from sentence_transformers import SentenceTransformer
                import torch
                
                device = "cpu" if backend_type == "local-cpu" else "cuda"
                
                if device == "cuda" and not torch.cuda.is_available():
                    logger.warning("CUDA not available, falling back to CPU")
                    device = "cpu"
                
                model = SentenceTransformer(
                    self.config.local_model_name,
                    device=device
                )
                
                logger.info(f"Local model loaded on {device}")
                return {
                    "type": "local",
                    "model": model,
                    "device": device
                }
            except ImportError:
                raise RuntimeError(
                    "sentence-transformers not installed. "
                    "Install with: pip install sentence-transformers torch"
                )
        
        raise ValueError(f"Unknown local backend: {backend_type}")
    
    async def embed(self, text: str) -> List[float]:
        """単一テキストのEmbedding生成
        
        Args:
            text: Embedding化するテキスト
            
        Returns:
            Embeddingベクトル（float配列）
            
        Raises:
            RuntimeError: モデルが未ロードの場合
            
        Requirements: 2.2
        """
        if not self._is_loaded or self.backend is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            backend_type = self.backend["type"]
            
            if backend_type == "gemini":
                result = self.backend["client"].embed_content(
                    model="models/text-embedding-004",
                    content=text,
                    task_type="retrieval_document"
                )
                return result['embedding']
            
            elif backend_type == "openai":
                response = await self.backend["client"].embeddings.create(
                    model=self.backend["model"],
                    input=text
                )
                return response.data[0].embedding
            
            elif backend_type == "local":
                embedding = self.backend["model"].encode(
                    text,
                    convert_to_numpy=True,
                    normalize_embeddings=self.config.normalize_embeddings,
                    show_progress_bar=False
                )
                return embedding.tolist()
            
            raise ValueError(f"Unknown backend type: {backend_type}")
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise RuntimeError(f"Failed to generate embedding: {e}") from e
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """バッチ処理でEmbedding生成
        
        Args:
            texts: Embedding化するテキストのリスト
            
        Returns:
            Embeddingベクトルのリスト
            
        Raises:
            RuntimeError: モデルが未ロードの場合
            
        Requirements: 2.2
        """
        if not self._is_loaded or self.backend is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        if not texts:
            return []
        
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts")
            backend_type = self.backend["type"]
            
            if backend_type == "gemini":
                # Gemini doesn't have batch API, process sequentially
                embeddings = []
                for text in texts:
                    result = self.backend["client"].embed_content(
                        model="models/text-embedding-004",
                        content=text,
                        task_type="retrieval_document"
                    )
                    embeddings.append(result['embedding'])
                return embeddings
            
            elif backend_type == "openai":
                response = await self.backend["client"].embeddings.create(
                    model=self.backend["model"],
                    input=texts
                )
                return [item.embedding for item in response.data]
            
            elif backend_type == "local":
                embeddings = self.backend["model"].encode(
                    texts,
                    batch_size=self.config.batch_size,
                    convert_to_numpy=True,
                    normalize_embeddings=self.config.normalize_embeddings,
                    show_progress_bar=len(texts) > 10
                )
                return embeddings.tolist()
            
            raise ValueError(f"Unknown backend type: {backend_type}")
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise RuntimeError(f"Failed to generate batch embeddings: {e}") from e
    
    def is_loaded(self) -> bool:
        """モデルがロード済みかどうかを返す
        
        Returns:
            ロード済みの場合True
        """
        return self._is_loaded
    
    def get_embedding_dimension(self) -> Optional[int]:
        """Embeddingの次元数を返す
        
        Returns:
            Embedding次元数（モデル未ロードの場合はNone）
        """
        if not self._is_loaded or self.backend is None:
            return None
        
        backend_type = self.backend["type"]
        
        if backend_type == "gemini":
            return 768  # text-embedding-004 dimension
        elif backend_type == "openai":
            if "text-embedding-3-small" in self.backend["model"]:
                return 1536
            elif "text-embedding-3-large" in self.backend["model"]:
                return 3072
            return 1536  # default
        elif backend_type == "local":
            return self.backend["model"].get_sentence_embedding_dimension()
        
        return None
