import chromadb
from pathlib import Path

from document_intelligence.ingestion.pdf import extract_document
from document_intelligence.processing.document import clean_document
from document_intelligence.processing.semantic_chunker import SemanticChunker
from document_intelligence.processing.embedder import Embedder
from document_intelligence.storage.vector_storage import VectorStorage
from document_intelligence.retrieval.retriever import Retriever
from document_intelligence.generation.generator import Generator
from document_intelligence.generation.adapters import OpenRouterClient


def main():
    pdf_path = Path("tests/fixtures/documents/bachelor_of_computing_program.pdf")
    print(f"Ingesting: {pdf_path.name}...")

    document = extract_document(pdf_path)
    cleaned_doc = clean_document(document)

    print("Semantically chunking document...")
    embedder = Embedder()
    chunker = SemanticChunker(embedder=embedder)

    all_chunks = []
    for page in cleaned_doc.pages:
        page_chunks = chunker.chunk(
            text=page.text,
            file_name=cleaned_doc.file_name,
            page_no=page.page_number,
        )
        all_chunks.extend(page_chunks)

    embedded_chunks = embedder.embed_chunks(all_chunks)

    print(f"Indexing {len(embedded_chunks)} chunks in ChromaDB...")
    client = chromadb.Client()
    storage = VectorStorage(collection_name="demo_docs", client=client)
    storage.add_chunks(embedded_chunks)

    retriever = Retriever(embedder=embedder, vector_storage=storage)
    llm_client = OpenRouterClient()
    generator = Generator(llm_client=llm_client)

    question = "What is the recipe for chocolate chip cookies?"
    print(f"\nQuestion: {question}")
    print("🔍 Retrieving relevant context...")
    retrieved_chunks = retriever.retrieve_chunks(query=question, top_k=3)

    print("Generating grounded answer with citations...\n")
    response = generator.generate(query=question, chunks=retrieved_chunks)

    print("=" * 60)
    print("ANSWER:")
    print(response.answer)
    print("=" * 60)
    print(f"Cited Pages : {response.cited_pages}")
    print(f"Grounded    : {response.is_grounded}")


if __name__ == "__main__":
    main()
