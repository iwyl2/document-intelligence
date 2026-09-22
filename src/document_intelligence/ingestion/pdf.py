from pathlib import Path
from pypdf import PdfReader
from document_intelligence.models.document import DocumentPage, Document


def extract_document(file_path: str | Path) -> Document:
    """
    Extract text from a text-based PDF and return it as a Document.

    V1 supports text-based PDFs only.
    Scanned/image-only PDFs require OCR and are outside V1 scope.
    """

    file_path = Path(file_path)
    reader = PdfReader(file_path)

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        pages.append(DocumentPage(page_number=page_number, text=text))

    return Document(file_name=file_path.name, pages=pages)
