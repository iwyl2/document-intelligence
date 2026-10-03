from document_intelligence.processing.embedder import Embedder
from document_intelligence.storage.vector_storage import VectorStorage


class Retriever:
    def __init__(self, embedder: Embedder, vector_storage: VectorStorage):
        self.embedder = embedder
        self.vector_storage = vector_storage

    def retrieve(self, query: str, top_k: int = 3):
        query_embedding = self.embedder.encode(query)

        results = self.vector_storage.search(
            query_embedding=query_embedding, top_k=top_k
        )

        return results
