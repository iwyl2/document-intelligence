import chromadb
import numpy as np
import pytest

from document_intelligence.models.chunk import Chunk, EmbeddedChunk
from document_intelligence.storage.vector_storage import VectorStorage


@pytest.fixture
def memory_storage():
    """Provides an isolated, in-memory ChromaDB vector storage instance."""
    client = chromadb.Client()
    return VectorStorage(collection_name="test_default", client=client)


def create_embedded_chunk(text: str, file_name: str, embedding_val: float) -> EmbeddedChunk:
    """Helper to quickly instantiate test embedded chunks."""
    return EmbeddedChunk(
        chunk=Chunk(
            text=text,
            sentences=[text],
            file_name=file_name,
            page_no=1,
        ),
        embeddings=np.array([embedding_val] * 384, dtype=np.float32),
    )


def test_session_isolation(memory_storage):
    """
    Verifies that documents added to one session are completely isolated
    from documents added to another session.
    """
    chunk_alpha = create_embedded_chunk(
        text="Alpha session proprietary data.",
        file_name="alpha.pdf",
        embedding_val=0.1,
    )
    chunk_beta = create_embedded_chunk(
        text="Beta session confidential analysis.",
        file_name="beta.pdf",
        embedding_val=0.9,
    )

    # Index into two distinct sessions
    memory_storage.add_chunks([chunk_alpha], session_id="user_alpha")
    memory_storage.add_chunks([chunk_beta], session_id="user_beta")

    # 1. Verify counts are isolated
    assert memory_storage.count(session_id="user_alpha") == 1
    assert memory_storage.count(session_id="user_beta") == 1

    # 2. Verify indexed files are isolated
    assert memory_storage.get_indexed_files(session_id="user_alpha") == ["alpha.pdf"]
    assert memory_storage.get_indexed_files(session_id="user_beta") == ["beta.pdf"]

    # 3. Query user_alpha: should return ONLY alpha's chunk
    search_query = np.array([0.1] * 384, dtype=np.float32)
    alpha_results = memory_storage.search(query_embedding=search_query, session_id="user_alpha", top_k=5)
    alpha_docs = alpha_results.get("documents", [[]])[0]

    assert len(alpha_docs) == 1
    assert "Alpha session proprietary data." in alpha_docs
    assert "Beta session confidential analysis." not in alpha_docs

    # 4. Query user_beta: should return ONLY beta's chunk
    beta_results = memory_storage.search(query_embedding=search_query, session_id="user_beta", top_k=5)
    beta_docs = beta_results.get("documents", [[]])[0]

    assert len(beta_docs) == 1
    assert "Beta session confidential analysis." in beta_docs
    assert "Alpha session proprietary data." not in beta_docs


def test_selective_session_deletion(memory_storage):
    """
    Verifies that clearing one session leaves all other concurrent sessions intact.
    """
    chunk_alpha = create_embedded_chunk("Alpha Document", "alpha.pdf", 0.2)
    chunk_beta = create_embedded_chunk("Beta Document", "beta.pdf", 0.8)

    memory_storage.add_chunks([chunk_alpha], session_id="session_alpha")
    memory_storage.add_chunks([chunk_beta], session_id="session_beta")

    assert memory_storage.count(session_id="session_alpha") == 1
    assert memory_storage.count(session_id="session_beta") == 1

    # Purge only session_alpha
    memory_storage.clear(session_id="session_alpha")

    # Alpha must be 0, but Beta must remain completely intact
    assert memory_storage.count(session_id="session_alpha") == 0
    assert memory_storage.count(session_id="session_beta") == 1
    assert memory_storage.get_indexed_files(session_id="session_beta") == ["beta.pdf"]


def test_clear_non_existent_session_does_not_crash(memory_storage):
    """
    Verifies that attempting to clear an empty/uninitialized session
    fails gracefully without raising unhandled errors.
    """
    try:
        memory_storage.clear(session_id="uninitialized_session_xyz")
    except Exception as exc:
        pytest.fail(f"Clearing a non-existent session raised an unexpected exception: {exc}")


def test_backward_compatibility_without_session_id(memory_storage):
    """
    Verifies that omitting session_id falls back to the default collection,
    ensuring existing V1 workflows and tests continue to work seamlessly.
    """
    default_chunk = create_embedded_chunk("Default chunk text", "default.pdf", 0.5)

    # Calling without session_id
    memory_storage.add_chunks([default_chunk])

    assert memory_storage.count() == 1
    assert memory_storage.get_indexed_files() == ["default.pdf"]

    results = memory_storage.search(np.array([0.5] * 384, dtype=np.float32), top_k=1)
    docs = results.get("documents", [[]])[0]
    assert "Default chunk text" in docs

    memory_storage.clear()
    assert memory_storage.count() == 0
