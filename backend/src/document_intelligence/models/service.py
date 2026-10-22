from dataclasses import dataclass


@dataclass(frozen=True)
class IngestionResult:
    """Summary of an ingested and indexed document."""

    file_name: str
    num_pages: int
    num_chunks: int
