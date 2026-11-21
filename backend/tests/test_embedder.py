"""Tests for deployment-aware embedding model selection."""

from app.services import embedder


def test_render_defaults_to_lightweight_embeddings(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("USE_SENTENCE_TRANSFORMERS", raising=False)
    monkeypatch.setattr(embedder, "_EMBEDDING_MODEL", None)

    assert embedder._get_model() == "FALLBACK"


def test_sentence_transformers_can_be_enabled_explicitly(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("USE_SENTENCE_TRANSFORMERS", "true")

    assert embedder._sentence_transformers_enabled() is True
