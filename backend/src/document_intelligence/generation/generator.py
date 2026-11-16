import re
from typing import Any, List

from document_intelligence.models.generation import GenerationResponse
from document_intelligence.models.retriever import RetrievedChunk

SYSTEM_PROMPT = """You are an accurate, grounded document intelligence assistant.
Your task is to answer user questions strictly and exclusively based on the provided context chunks.

Rules:
1. Use ONLY the information provided within the <context> block. Do not extrapolate, assume, or use external knowledge.
2. For every factual claim you make, cite the source file and page using the exact format [file_name • Page X] (e.g. [syllabus.pdf • Page 2]). If only one document is present, use [file_name • Page X] consistently.
3. If the answer cannot be found in the provided context, respond EXACTLY with:
   "I cannot find this information in the provided document."
4. Do not mention "the context chunks" or "the provided text" in your explanation—speak directly about the document's contents.
"""


class Generator:
    FALLBACK_MESSAGE = "I cannot find this information in the provided document"

    def __init__(self, llm_client: Any, model_name: str = "gpt-4o-mini"):
        self.client = llm_client
        self.model = model_name

    def _format_context(self, chunks: List[RetrievedChunk]) -> str:
        context_block = []
        for i, chunk in enumerate(chunks, start=1):
            block = (
                f'<chunk_id="{i}" file="{chunk.file_name}" page="{chunk.page_number}">\n'
                f"{chunk.text.strip()}\n"
                f"</chunk>"
            )
            context_block.append(block)

        return "\n\n".join(context_block)

    def generate(self, query: str, chunks: List[RetrievedChunk]) -> GenerationResponse:
        if not chunks:
            return GenerationResponse(
                answer=self.FALLBACK_MESSAGE,
                cited_sources=[],
                cited_pages=[],
                is_grounded=False,
                raw_response=self.FALLBACK_MESSAGE,
            )

        context_str = self._format_context(chunks=chunks)
        prompt = (
            f"{SYSTEM_PROMPT}\n\n<context>\n{context_str}\n</context>\n\n"
            f"Question:{query}\nAnswer:"
        )

        raw_response = self.client.generate(prompt)

        if self.FALLBACK_MESSAGE.lower() in raw_response.lower():
            return GenerationResponse(
                answer=self.FALLBACK_MESSAGE,
                cited_sources=[],
                cited_pages=[],
                is_grounded=False,
                raw_response=raw_response,
            )

        # 1. Multi-document citations: [file_name • Page X] or [file_name • page X]
        multi_matches = re.findall(
            r"\[([^•\]]+?)\s*•\s*[Pp]age\s*(\d+)\]", raw_response
        )

        # 2. Single-document fallback: [Page X] or [page X]
        single_matches = re.findall(r"\[[Pp]age\s*(\d+)\]", raw_response)

        sources_set = set()
        for file_name, page_str in multi_matches:
            fn = file_name.strip()
            pg = int(page_str)
            sources_set.add((fn, pg))

        # If LLM used legacy [Page X] format and all chunks belong to one file, attribute to that file
        unique_context_files = list(
            dict.fromkeys(c.file_name for c in chunks if c.file_name)
        )
        if single_matches and len(unique_context_files) == 1:
            primary_file = unique_context_files[0]
            for page_str in single_matches:
                sources_set.add((primary_file, int(page_str)))

        sorted_sources = sorted(list(sources_set), key=lambda x: (x[0], x[1]))
        cited_sources = [
            {"file_name": fn, "page_number": pg} for fn, pg in sorted_sources
        ]
        cited_pages = sorted(list({pg for _, pg in sorted_sources}))

        return GenerationResponse(
            answer=raw_response.strip(),
            cited_sources=cited_sources,
            cited_pages=cited_pages,
            is_grounded=len(cited_sources) > 0,
            raw_response=raw_response,
        )
