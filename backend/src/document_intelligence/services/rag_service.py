from pathlib import Path
from typing import Optional

import chromadb
from document_intelligence.generation.adapters import OpenRouterClient
from document_intelligence.generation.generator import Generator
from document_intelligence.ingestion.pdf import extract_document
from document_intelligence.models.generation import GenerationResponse
from document_intelligence.processing.document import clean_document
from document_intelligence.models.service import IngestionResult
from document_intelligence.processing.embedder import (
    BaseEmbedder,
    LocalEmbedder,
    get_embedder,
)
from document_intelligence.processing.semantic_chunker import SemanticChunker
from document_intelligence.retrieval.retriever import Retriever
from document_intelligence.storage.vector_storage import VectorStorage


class RagService:
    """
    Application Service orchestrating ingestion, indexing, retrieval,
    and grounded generation.
    """

    def __init__(
        self,
        embedder: BaseEmbedder,
        chunker: SemanticChunker,
        storage: VectorStorage,
        retriever: Retriever,
        generator: Generator,
    ) -> None:
        """
        Accepts pre-configured dependencies.
        Allows easy mocking in tests and avoids reloading heavy models.
        """

        self.embedder = embedder
        self.chunker = chunker
        self.storage = storage
        self.retriever = retriever
        self.generator = generator

    @classmethod
    def create_default(
        cls,
        collection_name: str = "document_intelligence",
        chroma_client: Optional[chromadb.ClientAPI] = None,
        embedder: Optional[BaseEmbedder] = None,
    ) -> "RagService":
        """
        Factory method to initialize the service with production defaults
        Auto-selects LocalEmbedder or CloudEmbedder based on EMBEDDER_BACKEND.
        """

        if embedder is None:
            embedder = get_embedder()

        chunker = SemanticChunker(embedder=embedder)

        if chroma_client is None:
            chroma_client = chromadb.Client()

        storage = VectorStorage(collection_name=collection_name, client=chroma_client)
        retriever = Retriever(embedder=embedder, vector_storage=storage)
        generator = Generator(llm_client=OpenRouterClient())

        return cls(
            embedder=embedder,
            chunker=chunker,
            storage=storage,
            retriever=retriever,
            generator=generator,
        )

    def index_document(self, file_path: Path | str) -> IngestionResult:
        """
        Full ingestion pipeline:
        1. Extract pages from PDF (extract_document)
        2. Clean text per page (clean_document)
        3. Semantically chunk each page (chunker.chunk)
        4. Embed chunks (embedder.embed_chunks)
        5. Store in vector database (storage.add_chunks)
        Returns IngestionResult(file_name, num_pages, num_chunks).
        """

        document = extract_document(file_path=file_path)
        cleaned_doc = clean_document(document=document)

        all_chunks = []
        for page in cleaned_doc.pages:
            page_chunks = self.chunker.chunk(
                text=page.text, page_no=page.page_number, file_name=document.file_name
            )
            all_chunks.extend(page_chunks)

        if all_chunks:
            embedded_chunks = self.embedder.embed_chunks(chunks=all_chunks)
            self.storage.add_chunks(embedded_chunks=embedded_chunks)

        return IngestionResult(
            file_name=document.file_name,
            num_pages=len(document.pages),
            num_chunks=len(all_chunks),
        )

    def query(self, question: str, top_k: int = 3) -> GenerationResponse:
        """
        RAG query pipeline:
        1. Retrieve top-k relevant chunks (retriever.retrieve_chunks)
        2. Generate grounded answer with citations (generator.generate)
        Returns GenerationResponse(answer, cited_pages, is_grounded).
        """
        retrieved_chunks = self.retriever.retrieve_chunks(query=question, top_k=top_k)
        return self.generator.generate(query=question, chunks=retrieved_chunks)

    def get_status(self) -> dict:
        """Inspect the current in-memory vector storage status."""
        total_chunks = self.storage.count()
        files = self.storage.get_indexed_files()
        return {
            "total_chunks": total_chunks,
            "indexed_files": files,
            "is_empty": total_chunks == 0,
        }

    def clear_index(self) -> dict:
        """Clear all indexed documents and chunks from memory."""
        self.storage.clear()
        return {
            "message": "In-memory vector store successfully cleared.",
            "total_chunks": 0,
        }
