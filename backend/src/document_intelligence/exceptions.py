class DocumentIngestionError(Exception):
    """Base exception for document ingestion errors."""


class DocumentNotFoundError(DocumentIngestionError):
    """Raised when the requested document doesn't exists."""


class DocumentReadError(DocumentIngestionError):
    """Raised when a document cannot be read or parsed."""
