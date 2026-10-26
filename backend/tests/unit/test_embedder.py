import os
from unittest.mock import MagicMock, patch
import numpy as np
from sentence_transformers import util
from document_intelligence.models.chunk import Chunk
from document_intelligence.processing.embedder import (
    BaseEmbedder,
    CloudEmbedder,
    LocalEmbedder,
    get_embedder,
)


def test_text_embedding_shape_and_type():
    embedder = LocalEmbedder()
    text = "Hello world"

    embed = embedder.encode(text)

    assert isinstance(embed, np.ndarray), f"Expected numpy array, got {type(embed)}"
    assert embed.shape == (384,), f"Expected shape (384,), got {embed.shape}"
    assert not np.isnan(embed).any(), "Embedding contains NaN values"
    assert not np.isinf(embed).any(), "Embedding contains Infinite values"


def test_local_embedder_batch_encoding():
    embedder = LocalEmbedder()
    texts = ["First test sentence.", "Second test sentence."]

    embeddings = embedder.encode(texts)

    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape == (2, 384)
    assert not np.isnan(embeddings).any()


def test_embed_chunks_uses_batch_encoding():
    embedder = LocalEmbedder()
    chunks = [
        Chunk(text="Chunk one content.", sentences=["Chunk one content."], file_name="doc.pdf", page_no=1),
        Chunk(text="Chunk two content.", sentences=["Chunk two content."], file_name="doc.pdf", page_no=1),
    ]

    embedded_chunks = embedder.embed_chunks(chunks)

    assert len(embedded_chunks) == 2
    assert embedded_chunks[0].chunk.text == "Chunk one content."
    assert embedded_chunks[0].embeddings.shape == (384,)
    assert embedded_chunks[1].chunk.text == "Chunk two content."
    assert embedded_chunks[1].embeddings.shape == (384,)


def test_embedding_semantic_similarity():
    """Assert semantic behavior using cosine similarity."""
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


@patch("httpx.Client.post")
def test_cloud_embedder_single_and_batch_mocked(mock_post):
    fake_single_response = MagicMock()
    fake_single_response.status_code = 200
    fake_single_response.json.return_value = {
        "embedding": {"values": [0.1] * 384}
    }

    fake_batch_response = MagicMock()
    fake_batch_response.status_code = 200
    fake_batch_response.json.return_value = {
        "embeddings": [
            {"values": [0.2] * 384},
            {"values": [0.3] * 384},
        ]
    }

    mock_post.side_effect = [fake_single_response, fake_batch_response]

    cloud_embedder = CloudEmbedder(api_key="test-key-123")

    single_emb = cloud_embedder.encode("Test query")
    assert single_emb.shape == (384,)
    assert np.isclose(single_emb[0], 0.1)

    batch_emb = cloud_embedder.encode(["Sentence A", "Sentence B"])
    assert batch_emb.shape == (2, 384)
    assert np.isclose(batch_emb[0, 0], 0.2)
    assert np.isclose(batch_emb[1, 0], 0.3)


def test_get_embedder_factory():
    local_inst = get_embedder("local")
    assert isinstance(local_inst, LocalEmbedder)

    with patch.dict(os.environ, {"GEMINI_API_KEY": "dummy-key"}):
        cloud_inst = get_embedder("cloud")
        assert isinstance(cloud_inst, CloudEmbedder)
