from dataclasses import dataclass
from typing import Optional


@dataclass
class RetrievedChunk:
    text: str
    file_name: str
    page_number: int
    distance: Optional[float] = None
