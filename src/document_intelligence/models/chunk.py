from dataclasses import dataclass

@dataclass
class Chunk:
    text:str
    sentences:list[str]