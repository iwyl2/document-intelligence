from typing import List

from document_intelligence.models.retriever import RetrievedChunk

SYSTEM_PROMPT = """You are an accurate, grounded document intelligence assistant.
Your task is to answer user questions strictly and exclusively based on the provided context chunks.

Rules:
1. Use ONLY the information provided within the <context> block. Do not extrapolate, assume, or use external knowledge.
2. For every factual claim you make, you MUST cite the source page inline using the format [Page X] (e.g., "...focuses on software engineering [Page 2].").
3. If the answer cannot be found in the provided context, respond EXACTLY with:
   "I cannot find this information in the provided document."
4. Do not mention "the context chunks" or "the provided text" in your explanation—speak directly about the document's contents.
"""


class Generator:
    FALLBACK_MESSAGE = "I cannot find this information in the provided document"

    def __init__(self, llm_client: Any, model_name: str = "gpt-4o-mini"):
        self.client = llm_client
        self.model = model_name

    def format_context(self, chunks: List[RetrievedChunk]) -> str:
        context_block = []
        for i, chunk in enumerate(chunks, start=1):
            block = (
                f'<chunk_id="{i}" file="{chunk.file_name}" page="{chunk.page_number}">\n'
                f"{chunk.text.strip()}\n"
                f"</chunk>"
            )
            context_block.append(block)

        return "\n\n".join(context_block)
