from document_intelligence.ingestion.pdf import extract_document
from document_intelligence.processing.document import clean_document
from document_intelligence.processing.semantic_chunker import SemanticChunker
from pathlib import Path

FIXTURES_DIR = Path("tests/fixtures/documents")

def test_chunking():
    document_path = FIXTURES_DIR/ "bachelor_of_computing_program.pdf"

    document = extract_document(document_path)

    cleaned_document = clean_document(document)

    chunker = SemanticChunker()
    chunks = []

    for page in cleaned_document.pages:
        page_chunks = chunker.chunk(
            text=page.text,
            file_name=cleaned_document.file_name,
            page_no=page.page_number
        )

        chunks.extend(page_chunks)

    assert len(chunks) > 0

    for chunk in chunks:
        assert chunk.text
        assert chunk.sentences
        assert chunk.file_name == cleaned_document.file_name
        assert chunk.page_no > 0

        print(
            f"\n[{chunk.file_name} | Page {chunk.page_no}]"
        )
        print(chunk.text)