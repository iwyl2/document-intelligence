from document_intelligence.processing.semantic_chunker import SemanticChunker
from document_intelligence.processing.embedder import Embedder


def test_semantic_chunker():
    text = """
    The Bachelor of Computing program provides students with
    fundamental knowledge in software engineering and programming.

    Students are required to complete an industrial training
    period during the final stage of the program.

    The industrial training provides students with practical
    experience in a professional working environment.

    Students must submit their training documentation before
    the completion of the program.

    The university library is open from 8 AM to 5 PM.

    Students can access the library during weekdays.
    """

    embedder = Embedder()
    chunker = SemanticChunker(embedder=embedder)

    chunks = chunker.chunk(text)

    assert len(chunks) > 0

    for chunk in chunks:
        assert chunk.text
        assert chunk.sentences

        print(f"\n--- Chunk ---")
        print(chunk.text)