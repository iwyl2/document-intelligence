import chromadb
from document_intelligence.exceptions import CollectionEmptyError
from document_intelligence.models.chunk import EmbeddedChunk
import re


class VectorStorage:
    def __init__(
        self, collection_name: str = "documents", path: str = "data/chroma", client=None
    ):
        self.client = client or chromadb.PersistentClient(path=path)

        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_chunks(
        self, embedded_chunks: list[EmbeddedChunk], session_id: str | None = None
    ) -> None:
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

        collection = self._get_collections(session_id=session_id)
        collection.add(
            ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas
        )

    def search(self, query_embedding, top_k: int = 3, session_id: str | None = None):
        collection = self._get_collections(session_id=session_id)
        results = collection.query(
            query_embeddings=[query_embedding.tolist()], n_results=top_k
        )

        return results

    def count(self, session_id: str | None = None) -> int:
        """Return total number of chunks indexed in the collection."""
        return self._get_collections(session_id=session_id).count()

    def get_indexed_files(self, session_id: str | None = None) -> list[str]:
        """Return distinct file names currently present in the collection."""
        collection = self._get_collections(session_id=session_id)
        data = collection.get(include=["metadatas"])

        if not data or not data["metadatas"]:
            return []

        files = {m["file_name"] for m in data["metadatas"] if m and "file_name" in m}
        return sorted(list(files))

    def clear(self, session_id: str | None = None) -> None:
        """Completely purge the collection and recreate a fresh empty one."""
        try:
            collection = self._get_collections(session_id=session_id)
            self.client.delete_collection(name=collection.name)
            if not session_id:
                self.collection = self.client.get_or_create_collection(
                    name=collection.name
                )
        except ValueError as er:
            raise CollectionEmptyError(f"Collection {collection.name} is empty")

    def _sanitize_collection_name(self, session_id: str) -> str:
        cleaned_id = re.sub(r"[^a-zA-Z0-9_-]", "_", session_id)
        return f"session_{cleaned_id}"[:63].rstrip("_-")

    def _get_collections(self, session_id: str | None = None) -> chromadb.Collection:
        if session_id:
            session_id = self._sanitize_collection_name(session_id=session_id)
            return self.client.get_or_create_collection(name=session_id)
        return self.collection
