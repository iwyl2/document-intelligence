import chromadb
from pathlib import Path

from document_intelligence.ingestion.pdf import extract_document
from document_intelligence.processing.document import clean_document
from document_intelligence.processing.semantic_chunker import SemanticChunker
from document_intelligence.processing.embedder import LocalEmbedder
from document_intelligence.retrieval.retriever import Retriever
from document_intelligence.storage.vector_storage import VectorStorage

FIXTURES_DIR = Path("tests/fixtures/documents")


EVALUATION_CASES = [
    {
        "question": "What is the Bachelor of Computing program?",
        "expected_terms": [
            "bachelor",
            "computing",
            "software development",
        ],
    },
    {
        "question": "What subjects are included in the Bachelor of Computing program?",
        "expected_terms": [
            "programming",
            "database systems",
            "computer networks",
            "software engineering",
            "information systems",
        ],
    },
    {
        "question": "What practical experience do students get?",
        "expected_terms": [
            "industrial training",
            "professional working environment",
        ],
    },
    {
        "question": "What assessment methods are used?",
        "expected_terms": [
            "examinations",
            "assignments",
            "practical activities",
            "project work",
        ],
    },
    {
        "question": "What facilities are available to students?",
        "expected_terms": [
            "computer laboratories",
            "library",
        ],
    },
]


def build_retriever():
    document_path = FIXTURES_DIR / "bachelor_of_computing_program.pdf"

    document = extract_document(document_path)

    assert document.pages

    cleaned_document = clean_document(document)

    embedder = LocalEmbedder()

    chunker = SemanticChunker(embedder=embedder)

    chunks = []

    for page in cleaned_document.pages:
        page_chunks = chunker.chunk(
            text=page.text,
            file_name=cleaned_document.file_name,
            page_no=page.page_number,
        )

        chunks.extend(page_chunks)

    assert chunks

    embedded_chunks = embedder.embed_chunks(chunks)

    assert len(embedded_chunks) == len(chunks)

    client = chromadb.Client()

    storage = VectorStorage(
        collection_name="retrieval_evaluation",
        client=client,
    )

    storage.add_chunks(embedded_chunks)

    stored_documents = storage.collection.get()

    assert len(stored_documents["documents"]) == len(embedded_chunks)

    return Retriever(
        embedder=embedder,
        vector_storage=storage,
    )


def test_retrieval_evaluation():
    retriever = build_retriever()

    successful_cases = 0

    for case in EVALUATION_CASES:
        question = case["question"]
        expected_terms = case["expected_terms"]

        chunks = retriever.retrieve_chunks(
            query=question,
            top_k=3,
        )

        assert len(chunks) > 0

        retrieved_text = " ".join(chunk.text for chunk in chunks).lower()

        matched_terms = [
            term for term in expected_terms if term.lower() in retrieved_text
        ]

        match_ratio = len(matched_terms) / len(expected_terms)

        print("\n")
        print("=" * 80)
        print(f"QUESTION: {question}")
        print("=" * 80)

        print(f"Expected terms: {len(expected_terms)}")

        print(f"Matched terms: {len(matched_terms)}")

        print(f"Match ratio: {match_ratio:.2%}")

        print(f"Matched: {matched_terms}")

        print(
            f"Missing: {[term for term in expected_terms if term.lower() not in retrieved_text]}"
        )

        for index, chunk in enumerate(chunks, start=1):
            print(f"\n--- RESULT {index} ---")
            print(f"File: {chunk.file_name} | Page: {chunk.page_number}")
            print(f"Distance: {chunk.distance}")
            print(chunk.text)

        if match_ratio >= 0.80:
            successful_cases += 1

    total_cases = len(EVALUATION_CASES)

    evaluation_score = successful_cases / total_cases

    print("\n")
    print("=" * 80)
    print("RETRIEVAL EVALUATION SUMMARY")
    print("=" * 80)

    print(f"Total cases: {total_cases}")
    print(f"Successful cases: {successful_cases}")
    print(f"Evaluation score: {evaluation_score:.2%}")

    assert successful_cases == total_cases
