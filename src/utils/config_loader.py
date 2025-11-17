# -*- coding: utf-8 -*-
"""設定ローダー - 環境変数から設定を読み込む"""

import os
from pathlib import Path
from src.models.config import LLMConfig, EmbeddingConfig, ChromaConfig


def load_llm_config() -> LLMConfig:
    """環境変数からLLM設定を読み込む
    
    Returns:
        LLM設定
    """
    return LLMConfig(
        backend=os.getenv("LLM_BACKEND", "gemini"),
        gemini_api_key=os.getenv("GOOGLE_API_KEY"),
        gemini_model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
        local_model_name=os.getenv("LLM_MODEL_NAME", "elyza/Llama-3-ELYZA-JP-8B"),
        max_length=int(os.getenv("LLM_MAX_LENGTH", "512")),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.7"))
    )


def load_embedding_config() -> EmbeddingConfig:
    """環境変数からEmbedding設定を読み込む
    
    Returns:
        Embedding設定
    """
    return EmbeddingConfig(
        backend=os.getenv("EMBEDDING_BACKEND", "gemini"),
        gemini_api_key=os.getenv("GOOGLE_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        local_model_name=os.getenv("EMBEDDING_MODEL_NAME", "intfloat/multilingual-e5-base"),
        batch_size=int(os.getenv("EMBEDDING_BATCH_SIZE", "32")),
        normalize_embeddings=os.getenv("NORMALIZE_EMBEDDINGS", "true").lower() == "true"
    )


def load_chroma_config() -> ChromaConfig:
    """環境変数からChroma設定を読み込む
    
    Returns:
        Chroma設定
    """
    return ChromaConfig(
        persist_dir=Path(os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")),
        collection_name=os.getenv("CHROMA_COLLECTION_NAME", "papersmith_papers"),
        distance_metric=os.getenv("CHROMA_DISTANCE_METRIC", "cosine")
    )
