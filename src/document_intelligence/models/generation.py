from dataclasses import dataclass
from typing import List


@dataclass
class GenerationResponse:
    answer: str
    citied_pages: List[int]
    is_grounded: bool
    raw_response: str
