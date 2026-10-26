from pathlib import Path

import chromadb

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
        "relevant_terms": [
            "strong foundation in computing",
            "software development",
        ],
    },
    {
        "question": "What subjects are included in the Bachelor of Computing program?",
        "relevant_terms": [
            "programming",
            "database systems",
            "computer networks",
            "software engineering",
            "information systems",
        ],
    },
    {
        "question": "What practical experience do students get?",
        "relevant_terms": [
            "industrial training",
            "professional working environment",
        ],
    },
    {
        "question": "What assessment methods are used?",
        "relevant_terms": [
            "examinations",
            "assignments",
            "practical activities",
            "project work",
        ],
    },
    {
        "question": "What facilities are available to students?",
        "relevant_terms": [
            "computer laboratories",
            "library",
        ],
    },
]


def build_retriever():
    document_path = FIXTURES_DIR / "bachelor_of_computing_program.pdf"

    document = extract_document(document_path)
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

    embedded_chunks = embedder.embed_chunks(chunks)

    client = chromadb.Client()

    storage = VectorStorage(
        collection_name="retrieval_metrics",
        client=client,
    )

    storage.add_chunks(embedded_chunks)

    return Retriever(
        embedder=embedder,
        vector_storage=storage,
    )


def is_relevant(document: str, relevant_terms: list[str]) -> bool:
    document = document.lower()

    return all(term.lower() in document for term in relevant_terms)


def recall_at_k(
    retrieved_documents: list[str],
    relevant_terms: list[str],
    k: int,
) -> float:

    top_k_documents = retrieved_documents[:k]

    for document in top_k_documents:
        if is_relevant(document, relevant_terms):
            return 1.0

    return 0.0


def reciprocal_rank(
    retrieved_documents: list[str],
    relevant_terms: list[str],
) -> float:

    for rank, document in enumerate(
        retrieved_documents,
        start=1,
    ):
        if is_relevant(document, relevant_terms):
            return 1.0 / rank

    return 0.0


def test_retrieval_metrics():

    retriever = build_retriever()

    recall_at_1_scores = []
    recall_at_3_scores = []
    recall_at_5_scores = []
    reciprocal_rank_scores = []

    for case in EVALUATION_CASES:

        question = case["question"]
        relevant_terms = case["relevant_terms"]

        chunks = retriever.retrieve_chunks(
            query=question,
            top_k=5,
        )

        retrieved_documents = [chunk.text for chunk in chunks]

        recall_1 = recall_at_k(
            retrieved_documents,
            relevant_terms,
            k=1,
        )

        recall_3 = recall_at_k(
            retrieved_documents,
            relevant_terms,
            k=3,
        )

        recall_5 = recall_at_k(
            retrieved_documents,
            relevant_terms,
            k=5,
        )

        mrr = reciprocal_rank(
            retrieved_documents,
            relevant_terms,
        )

        recall_at_1_scores.append(recall_1)
        recall_at_3_scores.append(recall_3)
        recall_at_5_scores.append(recall_5)
        reciprocal_rank_scores.append(mrr)

        print("\n" + "=" * 80)
        print(f"QUESTION: {question}")
        print("=" * 80)

        print(f"Recall@1: {recall_1:.2f}")
        print(f"Recall@3: {recall_3:.2f}")
        print(f"Recall@5: {recall_5:.2f}")
        print(f"Reciprocal Rank: {mrr:.3f}")

        for rank, document in enumerate(
            retrieved_documents,
            start=1,
        ):
            print(f"\n--- RESULT {rank} ---")
            print(document)

    mean_recall_1 = sum(recall_at_1_scores) / len(recall_at_1_scores)

    mean_recall_3 = sum(recall_at_3_scores) / len(recall_at_3_scores)

    mean_recall_5 = sum(recall_at_5_scores) / len(recall_at_5_scores)

    mean_mrr = sum(reciprocal_rank_scores) / len(reciprocal_rank_scores)

    print("\n")
    print("=" * 80)
    print("RETRIEVAL METRICS SUMMARY")
    print("=" * 80)

    print(f"Recall@1: {mean_recall_1:.2%}")
    print(f"Recall@3: {mean_recall_3:.2%}")
    print(f"Recall@5: {mean_recall_5:.2%}")
    print(f"MRR:      {mean_mrr:.3f}")
