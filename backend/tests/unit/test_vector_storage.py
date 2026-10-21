import chromadb
import numpy as np

from document_intelligence.models.chunk import Chunk, EmbeddedChunk
from document_intelligence.storage.vector_storage import VectorStorage


def test_add_chunks():
    client = chromadb.Client()

    storage = VectorStorage(
        collection_name="test_documents",
        client=client,
    )

    chunks = [
        EmbeddedChunk(
            chunk=Chunk(
                text="Students must maintain 80% attendance.",
                sentences=["Students must maintain 80% attendance."],
                file_name="academic.pdf",
                page_no=1,
            ),
            embeddings=np.array([0.1, 0.2, 0.3]),
        ),
        EmbeddedChunk(
            chunk=Chunk(
                text="The pass mark for Mathematics is 40.",
                sentences=["The pass mark for Mathematics is 40."],
                file_name="academic.pdf",
                page_no=2,
            ),
            embeddings=np.array([0.4, 0.5, 0.6]),
        ),
    ]

    storage.add_chunks(chunks)

    result = storage.collection.get()

    assert len(result["ids"]) == 2

    assert len(result["documents"]) == 2

    assert "Students must maintain 80% attendance." in result["documents"]

    assert "The pass mark for Mathematics is 40." in result["documents"]


def test_chunk_metadata_is_stored():
    client = chromadb.Client()

    storage = VectorStorage(
        collection_name="test_metadata",
        client=client,
    )

    chunk = EmbeddedChunk(
        chunk=Chunk(
            text="Students must complete industrial training.",
            sentences=["Students must complete industrial training."],
            file_name="academic.pdf",
            page_no=3,
        ),
        embeddings=np.array([0.2, 0.4, 0.6]),
    )

    storage.add_chunks([chunk])

    result = storage.collection.get()

    metadata = result["metadatas"][0]

    assert metadata["file_name"] == "academic.pdf"
    assert metadata["page_number"] == 3


def test_search_returns_most_similar_chunk():
    client = chromadb.Client()

    storage = VectorStorage(
        collection_name="test_search",
        client=client,
    )

    chunks = [
        EmbeddedChunk(
            chunk=Chunk(
                text="Students must maintain 80% attendance.",
                sentences=["Students must maintain 80% attendance."],
                file_name="academic.pdf",
                page_no=1,
            ),
            embeddings=np.array([1.0, 0.0, 0.0]),
        ),
        EmbeddedChunk(
            chunk=Chunk(
                text="The pass mark for Mathematics is 40.",
                sentences=["The pass mark for Mathematics is 40."],
                file_name="academic.pdf",
                page_no=2,
            ),
            embeddings=np.array([0.0, 1.0, 0.0]),
        ),
        EmbeddedChunk(
            chunk=Chunk(
                text="The library is open from 8 AM to 5 PM.",
                sentences=["The library is open from 8 AM to 5 PM."],
                file_name="academic.pdf",
                page_no=3,
            ),
            embeddings=np.array([0.0, 0.0, 1.0]),
        ),
    ]

    storage.add_chunks(chunks)

    query_embedding = np.array([0.0, 0.9, 0.1])

    results = storage.search(
        query_embedding=query_embedding,
        top_k=1,
    )

    assert len(results["documents"][0]) == 1

    retrieved_document = results["documents"][0][0]

    assert retrieved_document == "The pass mark for Mathematics is 40."
