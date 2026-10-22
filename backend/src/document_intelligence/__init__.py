from pathlib import Path

from document_intelligence.services.rag_service import RagService


def main():
    rag_service = RagService.create_default()
    pdf_path = Path("tests/fixtures/documents/bachelor_of_computing_program.pdf")
    print(f"Ingesting: {pdf_path.name}...")

    result = rag_service.index_document(file_path=pdf_path)
    print(f"Indexed {result.num_chunks} chunks from {result.num_pages} pages.")

    question = "What practical experience do students get in the program?"
    response = rag_service.query(question=question, top_k=3)
    print(response.answer)


if __name__ == "__main__":
    main()
