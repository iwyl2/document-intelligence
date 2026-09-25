from dataclasses import dataclass

@dataclass
class Chunk:
    text:str
    sentences:list[str]
    file_name:str=""
    page_no:int=0