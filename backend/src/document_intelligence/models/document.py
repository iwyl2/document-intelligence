from dataclasses import dataclass


@dataclass
class DocumentPage:
    page_number: int
    text: str


@dataclass
class Document:
    file_name: str
    pages: list[DocumentPage]
