from dataclasses import dataclass, field
from typing import List


@dataclass
class GenerationResponse:
    answer: str
    cited_sources: list[dict]
    is_grounded: bool
    raw_response: str
    cited_pages: list[int] = field(default_factory=list)
