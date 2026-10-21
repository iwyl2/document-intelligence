import chromadb
import numpy as np

from document_intelligence.models.chunk import Chunk, EmbeddedChunk
from document_intelligence.retrieval.retriever import Retriever
from document_intelligence.storage.vector_storage import VectorStorage


class FakeEmbedder:
    def encode(self, text: str) -> np.ndarray:
        if "mathematics" in text.lower():
            return np.array([0.0, 1.0, 0.0])

        return np.array([1.0, 0.0, 0.0])


def test_retriever_returns_relevant_chunk():
    client = chromadb.Client()

    storage = VectorStorage(
        collection_name="test_retriever",
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
    ]

    storage.add_chunks(chunks)

    retriever = Retriever(
        embedder=FakeEmbedder(),
        vector_storage=storage,
    )

    results = retriever.retrieve_chunks(
        "What is the Mathematics pass mark?",
        top_k=1,
    )

    assert len(results) == 1
    assert results[0].text == "The pass mark for Mathematics is 40."
    assert results[0].file_name == "academic.pdf"
    assert results[0].page_number == 2
