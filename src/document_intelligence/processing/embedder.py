from sentence_transformers import SentenceTransformer
import numpy as np
from document_intelligence.models.chunk import Chunk,EmbeddedChunk

class Embedder:
    def __init__(self,model_name:str="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)


    def encode(self,text:str) -> np.ndarray:
        """
        This method will convert a given text to ndarray embedding
        """
        return self.model.encode(text)

    def embed_chunks(self,chunks:list[Chunk]) -> list[EmbeddedChunk]:
        """
        Convert the given list of chunks into a list of embedded chunks
        """

        embedded_chunks = []

        for chunk in chunks:
            e_chunk = EmbeddedChunk(
                chunk=chunk,
                embeddings=self.encode(chunk.text)
            )

            embedded_chunks.append(e_chunk)
