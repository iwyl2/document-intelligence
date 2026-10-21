from typing import List

from document_intelligence.models.retriever import RetrievedChunk
from document_intelligence.processing.embedder import Embedder
from document_intelligence.storage.vector_storage import VectorStorage


class Retriever:
    def __init__(self, embedder: Embedder, vector_storage: VectorStorage):
        self.embedder = embedder
        self.vector_storage = vector_storage

    def _retrieve(self, query: str, top_k: int):
        query_embedding = self.embedder.encode(query)

        results = self.vector_storage.search(
            query_embedding=query_embedding, top_k=top_k
        )

        return results

    def retrieve_chunks(self, query: str, top_k: int = 3) -> List[RetrievedChunk]:
        results = self._retrieve(query=query, top_k=top_k)
        chunks = []

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dis in zip(documents, metadatas, distances):
            chunk = RetrievedChunk(
                text=doc,
                file_name=meta.get("file_name", "unknown"),
                page_number=meta.get("page_number", 0),
                distance=dis,
            )
            chunks.append(chunk)

        return chunks
