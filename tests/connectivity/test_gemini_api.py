# -*- coding: utf-8 -*-
"""Gemini API connectivity tests

Real API tests to verify Gemini integration works correctly.
These tests require GOOGLE_API_KEY in .env file.

Requirements: 12.2, 12.3, 12.7, 12.8
"""

import pytest
import os
from dotenv import load_dotenv

from src.services.llm_service import LLMService
from src.services.embedding_service import EmbeddingService
from src.models.config import LLMConfig, EmbeddingConfig


# Load .env file
load_dotenv()


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.asyncio
async def test_gemini_llm_connectivity():
    """Gemini LLM API connectivity test
    
    Verifies that:
    - API key is valid
    - Model loads successfully
    - Generation works
    - Response format is correct
    
    Requirements: 12.7, 2.5
    """
    # Skip if no API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        pytest.skip("GOOGLE_API_KEY not set in .env")
    
    # Create service with Gemini backend
    config = LLMConfig(
        backend="gemini",
        gemini_api_key=api_key,
        gemini_model_name="gemini-2.0-flash"  # Use gemini-2.0-flash (current stable model)
    )
    service = LLMService(config)
    
    # Load model
    await service.load_model()
    assert service.is_loaded()
    assert service.backend["type"] == "gemini"
    
    # Test generation with simple prompt
    question = "What is 2+2?"
    context = "This is a basic math question."
    
    answer = await service.generate(
        question=question,
        context=context,
        max_length=100,
        temperature=0.1  # Low temperature for deterministic response
    )
    
    # Verify response
    assert isinstance(answer, str)
    assert len(answer) > 0
    # Should contain "4" somewhere in the answer
    assert "4" in answer or "four" in answer.lower()
    
    print(f"\n✓ Gemini LLM connectivity test passed")
    print(f"  Question: {question}")
    print(f"  Answer: {answer[:100]}...")


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.asyncio
async def test_gemini_embedding_connectivity():
    """Gemini Embedding API connectivity test
    
    Verifies that:
    - API key is valid
    - Model loads successfully
    - Embedding generation works
    - Response format is correct
    
    Requirements: 12.7, 2.2
    """
    # Skip if no API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        pytest.skip("GOOGLE_API_KEY not set in .env")
    
    # Create service with Gemini backend
    config = EmbeddingConfig(
        backend="gemini",
        gemini_api_key=api_key
    )
    service = EmbeddingService(config)
    
    # Load model
    await service.load_model()
    assert service.is_loaded()
    assert service.backend["type"] == "gemini"
    
    # Test single embedding
    text = "This is a test sentence for embedding."
    embedding = await service.embed(text)
    
    # Verify response
    assert isinstance(embedding, list)
    assert len(embedding) == 768  # Gemini text-embedding-004 dimension
    assert all(isinstance(x, float) for x in embedding)
    
    # Test batch embedding
    texts = [
        "First test sentence.",
        "Second test sentence.",
        "Third test sentence."
    ]
    embeddings = await service.embed_batch(texts)
    
    # Verify batch response
    assert isinstance(embeddings, list)
    assert len(embeddings) == 3
    assert all(len(emb) == 768 for emb in embeddings)
    
    # Verify embeddings are different
    assert embeddings[0] != embeddings[1]
    assert embeddings[1] != embeddings[2]
    
    print(f"\n✓ Gemini Embedding connectivity test passed")
    print(f"  Single embedding dimension: {len(embedding)}")
    print(f"  Batch embeddings count: {len(embeddings)}")


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.asyncio
async def test_gemini_error_handling():
    """Gemini API error handling test
    
    Verifies that invalid API keys are handled correctly.
    
    Requirements: 12.7, 8.5
    """
    # Create service with invalid API key
    config = LLMConfig(
        backend="gemini",
        gemini_api_key="invalid_key_12345",
        gemini_model_name="gemini-2.0-flash"
    )
    service = LLMService(config)
    
    # Load model (doesn't validate API key yet)
    await service.load_model()
    
    # Should raise error on actual API call
    with pytest.raises(RuntimeError) as exc_info:
        await service.generate(
            question="Test question",
            context="Test context"
        )
    
    # Verify error message is informative
    error_msg = str(exc_info.value)
    assert "Failed to generate answer" in error_msg
    
    print(f"\n✓ Gemini error handling test passed")
    print(f"  Error message: {error_msg[:100]}...")
