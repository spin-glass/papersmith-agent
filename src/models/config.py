"""設定モデル"""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ChromaConfig(BaseModel):
    """Chroma設定

    Requirements: 2.3
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "persist_dir": "./data/chroma",
                "collection_name": "papersmith_papers",
                "distance_metric": "cosine"
            }
        }
    )

    persist_dir: Path = Field(
        default=Path("./data/chroma"),
        description="Chroma永続化ディレクトリ"
    )
    collection_name: str = Field(
        default="papersmith_papers",
        description="コレクション名"
    )
    distance_metric: str = Field(
        default="cosine",
        description="距離メトリック (cosine/l2/ip)"
    )


class LLMConfig(BaseModel):
    """LLM設定

    Requirements: 2.3
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "backend": "gemini",
                "gemini_api_key": "your-api-key",
                "gemini_model_name": "gemini-1.5-flash",
                "max_length": 512,
                "temperature": 0.7
            }
        }
    )

    backend: str = Field(
        default="gemini",
        description="バックエンド (gemini/openai/local-cpu/local-mlx/local-cuda)"
    )
    # Gemini settings
    gemini_api_key: Optional[str] = Field(
        default=None,
        description="Google Gemini APIキー"
    )
    gemini_model_name: str = Field(
        default="gemini-2.0-flash",
        description="Geminiモデル名"
    )
    # OpenAI settings
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI APIキー"
    )
    openai_model_name: str = Field(
        default="gpt-4o-mini",
        description="OpenAIモデル名"
    )
    # Local model settings
    local_model_name: str = Field(
        default="elyza/Llama-3-ELYZA-JP-8B",
        description="ローカルモデル名 (HuggingFace ID)"
    )
    # Generation settings
    max_length: int = Field(
        default=512,
        description="最大生成トークン数"
    )
    temperature: float = Field(
        default=0.7,
        description="生成温度"
    )


class EmbeddingConfig(BaseModel):
    """Embedding設定

    Requirements: 2.3
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "backend": "gemini",
                "gemini_api_key": "your-api-key",
                "batch_size": 32,
                "normalize_embeddings": True
            }
        }
    )

    backend: str = Field(
        default="gemini",
        description="バックエンド (gemini/openai/local-cpu/local-mlx/local-cuda)"
    )
    # Gemini settings
    gemini_api_key: Optional[str] = Field(
        default=None,
        description="Google Gemini APIキー"
    )
    # OpenAI settings
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI APIキー"
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI Embeddingモデル名"
    )
    # Local model settings
    local_model_name: str = Field(
        default="intfloat/multilingual-e5-base",
        description="ローカルEmbeddingモデル名 (HuggingFace ID)"
    )
    batch_size: int = Field(
        default=32,
        description="バッチサイズ"
    )
    normalize_embeddings: bool = Field(
        default=True,
        description="Embeddingを正規化するか"
    )
