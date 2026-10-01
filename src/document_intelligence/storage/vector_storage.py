import chromadb
from document_intelligence.models.chunk import EmbeddedChunk


class VectorStorage:
    def __init__(
        self, collection_name: str = "documents", path: str = "data/chroma", client=None
    ):
        self.client = client or chromadb.PersistentClient(path=path)

        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_chunks(self, embedded_chunks: list[EmbeddedChunk]) -> None:
        ids = []
        documents = []
        embeddings = []
        metadatas = []

        for index, embedded_chunk in enumerate(embedded_chunks):
            chunk = embedded_chunk.chunk

            chunk_id = f"{chunk.file_name}" f"-page-{chunk.page_no}" f"-chunk-{index}"

            ids.append(chunk_id)
            documents.append(chunk.text)
            embeddings.append(embedded_chunk.embeddings.tolist())

            metadatas.append(
                {"file_name": chunk.file_name, "page_number": chunk.page_no}
            )

        self.collection.add(
            ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas
        )

    def search(self, query_embedding, top_k: int = 3):
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()], n_results=top_k
        )

        return results
