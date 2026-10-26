from document_intelligence.models.chunk import Chunk

import numpy as np
from document_intelligence.processing.embedder import BaseEmbedder


class SemanticChunker:
    def __init__(self, embedder: BaseEmbedder, percentile: float = 80.0):
        self.embedder = embedder
        self.percentile = percentile

    def split_sentences(self, text: str) -> list[str]:
        """
        Basic sentence splitting for V1.

        This is intentionally simple. We can replace it with
        a proper NLP sentence tokenizer later.
        """

        text = " ".join(text.split())

        sentences = []

        for sentence in text.split("."):
            sentence = sentence.strip()

            if sentence:
                sentences.append(sentence + ".")

        return sentences

    def calculate_similarity(self, embeddings: np.ndarray) -> list[float]:
        """
        Calculate cosine similarity between adjacent sentences.
        Includes guard against zero-norm division.
        """

        similarities = []

        for i in range(len(embeddings) - 1):
            current = embeddings[i]
            next_sentence = embeddings[i + 1]

            norm_current = np.linalg.norm(current)
            norm_next = np.linalg.norm(next_sentence)

            if norm_current == 0.0 or norm_next == 0.0:
                similarity = 0.0
            else:
                similarity = np.dot(current, next_sentence) / (
                    norm_current * norm_next
                )

            similarities.append(float(similarity))

        return similarities

    def find_boundaries(self, similarities: list[float]) -> list[int]:
        """
        Find semantic boundaries using similarity drops.

        A large drop indicates that the next sentence is
        semantically different from the previous sentence.
        """

        if not similarities:
            return []

        drops = []

        for i in range(len(similarities) - 1):
            drop = similarities[i] - similarities[i + 1]
            drops.append(drop)

        if not drops:
            return []

        threshold = np.percentile(drops, self.percentile)

        boundaries = []

        for i, drop in enumerate(drops):
            if drop >= threshold:
                boundaries.append(i + 1)

        return boundaries

    def create_chunks(
        self,
        sentences: list[str],
        boundaries: list[int],
        file_name: str = "",
        page_no: int = 0,
    ) -> list[Chunk]:
        """
        Combine sentences into chunks using the detected boundaries.
        """

        chunks = []

        start = 0

        for boundary in boundaries:
            chunk_sentence = sentences[start:boundary]

            if chunk_sentence:
                chunks.append(
                    Chunk(
                        text=" ".join(chunk_sentence),
                        sentences=chunk_sentence,
                        file_name=file_name,
                        page_no=page_no,
                    )
                )

            start = boundary

        remaining = sentences[start:]

        chunks.append(
            Chunk(
                text=" ".join(remaining),
                sentences=remaining,
                file_name=file_name,
                page_no=page_no,
            )
        )

        return chunks

    def chunk(self, text: str, file_name: str = "", page_no: int = 0) -> list[Chunk]:
        """
        Complete semantic chunking pipeline.
        """

        sentences = self.split_sentences(text)

        if not sentences:
            return []

        if len(sentences) == 1:
            return [
                Chunk(
                    text=sentences[0],
                    sentences=sentences,
                    file_name=file_name,
                    page_no=page_no,
                )
            ]

        embeddings = self.embedder.encode(sentences)

        similarities = self.calculate_similarity(embeddings)

        boundaries = self.find_boundaries(similarities)

        return self.create_chunks(
            sentences=sentences,
            boundaries=boundaries,
            file_name=file_name,
            page_no=page_no,
        )
