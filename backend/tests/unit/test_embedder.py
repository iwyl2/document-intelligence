import numpy as np
from sentence_transformers import util
from document_intelligence.processing.embedder import LocalEmbedder


def test_text_embedding_shape_and_type():
    embedder = LocalEmbedder()
    text = "Hello world"

    embed = embedder.encode(text)

    assert isinstance(embed, np.ndarray), f"Expected numpy array, got {type(embed)}"

    assert embed.shape == (384,), f"Expected shape (384,), got {embed.shape}"

    assert not np.isnan(embed).any(), "Embedding contains NaN values"
    assert not np.isinf(embed).any(), "Embedding contains Infinite values"


def test_embedding_semantic_similarity():
    """Optional: Assert semantic behavior using cosine similarity."""
    embedder = LocalEmbedder()

    vec1 = embedder.encode("The quick brown fox jumps over the lazy dog")
    vec2 = embedder.encode("A fast brown fox leaps over a sleepy hound")
    vec3 = embedder.encode("Quantum computing uses qubits for processing")

    similarity_related = util.cos_sim(vec1, vec2).item()
    similarity_unrelated = util.cos_sim(vec1, vec3).item()

    assert similarity_related > similarity_unrelated, (
        f"Expected related similarity ({similarity_related:.2f}) "
        f"to be greater than unrelated similarity ({similarity_unrelated:.2f})"
    )
