import chromadb
from pathlib import Path

from document_intelligence.ingestion.pdf import extract_document
from document_intelligence.processing.document import clean_document
from document_intelligence.processing.semantic_chunker import SemanticChunker
from document_intelligence.processing.embedder import LocalEmbedder
from document_intelligence.retrieval.retriever import Retriever
from document_intelligence.storage.vector_storage import VectorStorage

FIXTURES_DIR = Path("tests/fixtures/documents")


def test_document_retrieval():
    document_path = FIXTURES_DIR / "bachelor_of_computing_program.pdf"

    document = extract_document(document_path)

    assert document.pages

    cleaned_document = clean_document(document)

    embedder = LocalEmbedder()

    chunker = SemanticChunker(embedder=embedder)

    chunks = []

    for page in cleaned_document.pages:
        page_chunks = chunker.chunk(
            text=page.text,
            file_name=cleaned_document.file_name,
            page_no=page.page_number,
        )

        chunks.extend(page_chunks)

    assert len(chunks) > 0

    embedded_chunks = embedder.embed_chunks(chunks)

    assert len(embedded_chunks) == len(chunks)

    client = chromadb.Client()

    storage = VectorStorage(
        collection_name="integration_retrieval",
        client=client,
    )

    storage.add_chunks(embedded_chunks)

    stored_documents = storage.collection.get()

    assert len(stored_documents["documents"]) == len(embedded_chunks)

    retriever = Retriever(
        embedder=embedder,
        vector_storage=storage,
    )

    retrieved_chunks = retriever.retrieve_chunks(
        query="What is the Bachelor of Computing program?",
        top_k=3,
    )

    assert len(retrieved_chunks) > 0
    assert retrieved_chunks[0].file_name == cleaned_document.file_name
    assert retrieved_chunks[0].page_number > 0

    combined_text = " ".join(chunk.text for chunk in retrieved_chunks).lower()

    assert "bachelor" in combined_text
    assert "computing" in combined_text
