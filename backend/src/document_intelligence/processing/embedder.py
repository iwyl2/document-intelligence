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
    def encode(self, text: str) -> np.ndarray:
        """Every child must implement this method"""
        pass

    def embed_chunks(self, chunks: list[Chunk]) -> list[EmbeddedChunk]:
        """
        Convert the given list of chunks into a list of embedded chunks
        """
        embedded_chunks = []
        for chunk in chunks:
            e_chunk = EmbeddedChunk(chunk=chunk, embeddings=self.encode(chunk.text))
            embedded_chunks.append(e_chunk)

        return embedded_chunks


class LocalEmbedder(BaseEmbedder):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def encode(self, text: str) -> np.ndarray:
        """
        This method will convert a given text to ndarray embedding
        """
        return self.model.encode(text, convert_to_numpy=True)


class CloudEmbedder(BaseEmbedder):
    """
    Cloud embedder powered by Google Gemini (text-embedding-004) REST API.
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

        self.url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model_name}:embedContent?key={self.api_key}"
        )

    def encode(self, text: str) -> np.ndarray:
        """Fetch 384-dimensional embedding vector from Gemini REST API."""
        payload = {
            "model": f"models/{self.model_name}",
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": self.dimensions,
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(self.url, json=payload)
            response.raise_for_status()
            data = response.json()

        values = data["embedding"]["values"]
        return np.array(values, dtype=np.float32).reshape(-1)


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
