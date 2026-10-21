from document_intelligence.models.document import Document
from document_intelligence.processing.text import clean_text


def clean_document(document: Document) -> Document:
    """
    Clean the text of every page in a document.
    """
    for page in document.pages:
        page.text = clean_text(page.text)

    return document
