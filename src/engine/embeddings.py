"""
Embedding-based semantic validation.
Uses Gemini embedding model for destination verification via cosine similarity.
"""

from __future__ import annotations
import os
import numpy as np
from google import genai
import asyncio

def cosine_similarity(vec_a: list[float] | np.ndarray, vec_b: list[float] | np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec_a, dtype=np.float64)
    b = np.array(vec_b, dtype=np.float64)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

def _get_client():
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-project-id")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
    return genai.Client(vertexai=True, project=project, location=location)

async def get_text_embedding(
    text: str,
    model: str = "gemini-embedding-001",
) -> list[float]:
    """Get embedding vector from Gemini embedding model."""
    client = _get_client()

    def _embed() -> list[float]:
        response = client.models.embed_content(
            model=model,
            contents=text,
        )
        return response.embeddings[0].values

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _embed)

async def verify_destination(
    source_intent: str,
    destination_text: str,
    model: str = "gemini-embedding-001",
    threshold: float = 0.70,
) -> tuple[bool, float]:
    """
    Verify a navigation destination matches the source intent using
    embedding cosine similarity.
    """
    source_emb = await get_text_embedding(source_intent, model)
    dest_emb = await get_text_embedding(destination_text, model)
    score = cosine_similarity(source_emb, dest_emb)
    return score >= threshold, score
