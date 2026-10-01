import chromadb
from document_intelligence.models.chunk import EmbeddedChunk

class VectorStorage:
    def __init__(self,collection_name:str="documents"):
        self.client = chromadb.Client()

        self.collection = self.client.get_or_create_collection(name=collection_name)
        