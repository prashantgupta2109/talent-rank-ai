"""Singleton embedding service utilizing sentence-transformers with graceful fallback."""

import hashlib
import logging
import os
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Singleton model instance
_EMBEDDING_MODEL = None
_MODEL_NAME = "all-MiniLM-L6-v2"
_EMBEDDING_DIM = 384


def _sentence_transformers_enabled() -> bool:
    """Disable the heavyweight model by default on Render's constrained instances."""
    setting = os.getenv("USE_SENTENCE_TRANSFORMERS")
    if setting is not None:
        return setting.strip().lower() in {"1", "true", "yes", "on"}
    return os.getenv("RENDER", "").strip().lower() != "true"


def _get_model():
    """Retrieve or initialize the SentenceTransformer singleton instance."""
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        if not _sentence_transformers_enabled():
            logger.info("SentenceTransformer disabled; using deterministic semantic fallback")
            _EMBEDDING_MODEL = "FALLBACK"
            return _EMBEDDING_MODEL
        try:
            from sentence_transformers import SentenceTransformer
            _EMBEDDING_MODEL = SentenceTransformer(_MODEL_NAME)
            logger.info("Successfully loaded sentence-transformers model: %s", _MODEL_NAME)
        except Exception as e:
            logger.warning(
                "Could not load SentenceTransformer ('%s'). Utilizing deterministic semantic fallback. Detail: %s",
                _MODEL_NAME,
                str(e),
            )
            _EMBEDDING_MODEL = "FALLBACK"
    return _EMBEDDING_MODEL


def _fallback_embed(text: str) -> np.ndarray:
    """Generate a deterministic 384-dimensional normalized vector from text tokens."""
    vec = np.zeros(_EMBEDDING_DIM, dtype=np.float32)
    words = text.lower().split()
    if not words:
        return vec

    for word in words:
        # Seed pseudo-random projections from word hash
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        for i in range(4):
            idx = (h >> (i * 8)) % _EMBEDDING_DIM
            sign = 1.0 if ((h >> (i * 4)) & 1) else -1.0
            vec[idx] += sign

    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec


def embed(texts: List[str], batch_size: int = 32) -> np.ndarray:
    """Compute dense vector embeddings for a list of text strings with batching.

    Args:
        texts: List of strings to encode.
        batch_size: Processing batch size (default 32).

    Returns:
        2D numpy array of shape (len(texts), 384) with L2-normalized embeddings.
    """
    if not texts:
        return np.empty((0, _EMBEDDING_DIM), dtype=np.float32)

    model = _get_model()

    if model != "FALLBACK":
        try:
            embeddings = model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            return embeddings.astype(np.float32)
        except Exception as e:
            logger.warning("Error during model.encode, falling back: %s", str(e))

    # Fallback encoding
    matrix = np.empty((len(texts), _EMBEDDING_DIM), dtype=np.float32)
    for i, t in enumerate(texts):
        matrix[i] = _fallback_embed(t)
    return matrix


def compute_cosine_similarity(
    query_vecs: np.ndarray,
    doc_vecs: np.ndarray,
) -> np.ndarray:
    """Compute pairwise cosine similarities between query and document vectors.

    Args:
        query_vecs: 2D array of shape (N, D).
        doc_vecs: 2D array of shape (M, D).

    Returns:
        2D array of shape (N, M) with values in range [-1.0, 1.0].
    """
    if query_vecs.size == 0 or doc_vecs.size == 0:
        return np.empty((query_vecs.shape[0], doc_vecs.shape[0]), dtype=np.float32)

    # Compute dot product (since vectors are L2-normalized, dot product == cosine similarity)
    sims = np.dot(query_vecs, doc_vecs.T)
    return np.clip(sims, -1.0, 1.0)
