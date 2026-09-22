from pathlib import Path
from pypdf import PdfReader
from document_intelligence.models.document import DocumentPage, Document
from document_intelligence.exceptions import DocumentNotFoundError, DocumentReadError
from pypdf.errors import PdfReadError


def extract_document(file_path: str | Path) -> Document:
    """
    Extract text from a text-based PDF and return it as a Document.

    V1 supports text-based PDFs only.
    Scanned/image-only PDFs require OCR and are outside V1 scope.
    """

    file_path = Path(file_path)

    if not file_path.is_file():
        raise DocumentNotFoundError(f"Document not found: {file_path}")

    try:
        reader = PdfReader(file_path)

        pages = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""

            pages.append(DocumentPage(page_number=page_number, text=text))

        return Document(file_name=file_path.name, pages=pages)
    except PdfReadError as exc:
        raise DocumentReadError(f"Unable to read the pdf: {file_path}") from exc
    except PermissionError as exc:
        raise DocumentReadError(
            f"Permission denied while reading: {file_path}"
        ) from exc
