from document_intelligence.models.chunk import Chunk

import numpy as np
from sentence_transformers import SentenceTransformer

class SemanticChunker:
    def __init__(self,model_name:str="all-MiniLM-L6-v2",percentile:float=0.80):
        self.model = SentenceTransformer(model_name)
        self.percentile = percentile

    def split_sentences(self, text:str) -> list[str]:
        """
        Basic sentence splitting for V1.

        This is intentionally simple. We can replace it with
        a proper NLP sentence tokenizer later.
        """

        sentences = []

        for sentence in text.replace("\n"," ").split("."):
            sentence = sentence.strip()

            if sentence:
                sentences.append(sentence+".")

        return sentences

    def calculate_similarity(self,embeddings:np.ndarray) -> list[float]:
        """
        Calculate cosine similarity between adjacent sentences.
        """

        similarities = []

        for i in range (len(embeddings) - 1):
            current = embeddings[i]
            next_sentence = embeddings[i+1]

            similarity = np.dot(current,next_sentence)/(np.linalg.norm(current) * np.linalg.norm(next_sentence))

            similarities.append(float(similarity))

        return similarities

    def find_boundaries(self,similarities:list[float]) -> list[int]:
        """
        Find semantic boundaries using similarity drops.

        A large drop indicates that the next sentence is
        semantically different from the previous sentence.
        """

        if not similarities:
            return []

        drops = []

        for i in range(len(similarities)-1):
            drop = similarities[i] - similarities[i+1]
            drops.append(drop)

        if not drops:
            return []

        threshold = np.percentile(drops, self.percentile)

        boundaries = []

        for i,drop in enumerate(drops):
            if drop < threshold:
                boundaries.append(i+1)

        return boundaries

    def create_chunks(self,sentences:list[str], boundaries:list[int], file_name:str="", page_no:int=0) -> list[Chunk]:
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
                        page_no=page_no
                    )
                )

            start = boundary

        remaining = sentences[start:]

        chunks.append(
            Chunk(
                text=" ".join(remaining),
                sentences=remaining,
                file_name=file_name,
                page_no=page_no
            )
        )

        return chunks

    def chunk(self, text:str, file_name: str = "", page_no: int = 0)-> list[Chunk]:
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
                    page_no=page_no
                )
            ]

        embeddings = self.model.encode(
            sentences,
            normalize_embeddings=True
        )

        similarities = self.calculate_similarity(embeddings)

        boundaries = self.find_boundaries(similarities)

        return self.create_chunks(
            sentences=sentences,
            boundaries=boundaries,
            file_name=file_name,
            page_no=page_no
        )
