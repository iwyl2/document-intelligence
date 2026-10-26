import numpy as np
from document_intelligence.models.chunk import Chunk, EmbeddedChunk
from abc import ABC, abstractmethod
from dotenv import load_dotenv
import os
import httpx

load_dotenv()


class BaseEmbedder(ABC):
    """Abstract interface for all embedders"""

    @abstractmethod
    def encode(self, text: str | list[str]) -> np.ndarray:
        """
        Encode text into numpy embedding vectors.
        - If text is str: returns 1D array of shape (dimensions,)
        - If text is list[str]: returns 2D array of shape (len(text), dimensions)
        """
        pass

    def embed_chunks(self, chunks: list[Chunk]) -> list[EmbeddedChunk]:
        """
        Convert the given list of chunks into a list of embedded chunks
        using batch encoding for efficiency.
        """
        if not chunks:
            return []

        texts = [chunk.text for chunk in chunks]
        embeddings = self.encode(texts)

        return [
            EmbeddedChunk(chunk=chunk, embeddings=emb)
            for chunk, emb in zip(chunks, embeddings)
        ]


class LocalEmbedder(BaseEmbedder):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def encode(self, text: str | list[str]) -> np.ndarray:
        """
        Convert a given text or list of texts to ndarray embedding.
        - str -> 1D array of shape (384,)
        - list[str] -> 2D array of shape (N, 384)
        """
        if isinstance(text, list) and len(text) == 0:
            return np.empty((0, 384), dtype=np.float32)

        return self.model.encode(text, convert_to_numpy=True)


class CloudEmbedder(BaseEmbedder):
    """
    Cloud embedder powered by Google Gemini (gemini-embedding-001) REST API.
    Supports both single text strings and batched lists of strings.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gemini-embedding-001",
        dimensions: int = 384,
    ):
        self.api_key = (
            api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        )
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is not configured. "
                "Get a free key from https://aistudio.google.com/app/apikey"
            )

        self.model_name = model_name
        self.dimensions = dimensions
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def _encode_single(self, client: httpx.Client, text: str) -> np.ndarray:
        url = f"{self.base_url}/{self.model_name}:embedContent?key={self.api_key}"
        payload = {
            "model": f"models/{self.model_name}",
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": self.dimensions,
        }
        response = client.post(url, json=payload)
        response.raise_for_status()
        values = response.json()["embedding"]["values"]
        return np.array(values, dtype=np.float32).reshape(-1)

    def _encode_batch(self, client: httpx.Client, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.dimensions), dtype=np.float32)

        url = f"{self.base_url}/{self.model_name}:batchEmbedContents?key={self.api_key}"
        all_embeddings: list[list[float]] = []
        batch_size = 100

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            requests_payload = [
                {
                    "model": f"models/{self.model_name}",
                    "content": {"parts": [{"text": t}]},
                    "outputDimensionality": self.dimensions,
                }
                for t in batch
            ]
            response = client.post(url, json={"requests": requests_payload})
            response.raise_for_status()
            batch_result = response.json().get("embeddings", [])
            for item in batch_result:
                all_embeddings.append(item["values"])

        return np.array(all_embeddings, dtype=np.float32)

    def encode(self, text: str | list[str]) -> np.ndarray:
        """
        Fetch 384-dimensional embedding vector(s) from Gemini REST API.
        - str -> shape (384,)
        - list[str] -> shape (N, 384)
        """
        with httpx.Client(timeout=30.0) as client:
            if isinstance(text, str):
                return self._encode_single(client, text)
            elif isinstance(text, list):
                return self._encode_batch(client, text)
            else:
                raise TypeError(f"Expected str or list[str], got {type(text).__name__}")


def get_embedder(backend: str | None = None) -> BaseEmbedder:
    """
    Factory function to instantiate the configured BaseEmbedder.
    Inspects parameter or the EMBEDDER_BACKEND environment variable.
    Defaults to 'local'.
    """

    selected_backend = backend or os.getenv("EMBEDDER_BACKEND", "local").strip().lower()

    if selected_backend in ("cloud", "gemini"):
        return CloudEmbedder()
    elif selected_backend == "local":
        return LocalEmbedder()
    else:
        raise ValueError(
            f"Unsupported embedder backend: '{selected_backend}'. "
            "Supported backends are 'local' and 'cloud'."
        )
