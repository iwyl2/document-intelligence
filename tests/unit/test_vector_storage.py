import chromadb
import numpy as np

from document_intelligence.models.chunk import Chunk, EmbeddedChunk
from document_intelligence.storage.vector_storage import VectorStorage


def test_add_chunks():
    # Use an in-memory Chroma client for testing.
    # This keeps the test isolated from the real persistent database.
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

    # Add the embedded chunks to ChromaDB
    storage.add_chunks(chunks)

    # Retrieve everything from the collection
    result = storage.collection.get()

    # Verify that both chunks were stored
    assert len(result["ids"]) == 2

    # Verify that the documents were stored
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
