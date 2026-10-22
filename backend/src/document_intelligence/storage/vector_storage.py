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

    def count(self) -> int:
        """Return total number of chunks indexed in the collection."""
        return self.collection.count()

    def get_indexed_files(self) -> list[str]:
        """Return distinct file names currently present in the collection."""
        data = self.collection.get(include=["metadatas"])

        if not data or not data["metadatas"]:
            return []

        files = {m["file_name"] for m in data["metadatas"] if m and "file_name" in m}
        return sorted(list(files))

    def clear(self) -> None:
        """Completely purge the collection and recreate a fresh empty one."""
        self.client.delete_collection(name=self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name
        )
