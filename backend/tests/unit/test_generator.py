from document_intelligence.generation.generator import Generator
from document_intelligence.models.retriever import RetrievedChunk


class FakeLLMClient:
    """Mock LLM client for deterministic offline testing."""

    def __init__(self, response_text: str = ""):
        self.response_text = response_text
        self.calls = 0
        self.last_prompt = ""

    def generate(self, prompt: str) -> str:
        self.calls += 1
        self.last_prompt = prompt
        return self.response_text


def test_format_context_builds_xml_blocks():
    client = FakeLLMClient()
    generator = Generator(llm_client=client)

    chunks = [
        RetrievedChunk(
            text="First chunk content.",
            file_name="guide.pdf",
            page_number=1,
            distance=0.15,
        ),
        RetrievedChunk(
            text="Second chunk content.",
            file_name="guide.pdf",
            page_number=3,
            distance=0.25,
        ),
    ]

    formatted = generator._format_context(chunks)

    assert '<chunk_id="1" file="guide.pdf" page="1">' in formatted
    assert "First chunk content." in formatted
    assert "</chunk>" in formatted
    assert '<chunk_id="2" file="guide.pdf" page="3">' in formatted
    assert "Second chunk content." in formatted


def test_generate_returns_grounded_response_with_citations():
    fake_response = (
        "The Bachelor of Computing requires 80% attendance [bachelor.pdf • Page 1]. "
        "Students must pass with at least 40 marks [bachelor.pdf • Page 2]."
    )
    client = FakeLLMClient(response_text=fake_response)
    generator = Generator(llm_client=client)

    chunks = [
        RetrievedChunk(
            text="Attendance rule text",
            file_name="bachelor.pdf",
            page_number=1,
        ),
        RetrievedChunk(
            text="Passing marks text",
            file_name="bachelor.pdf",
            page_number=2,
        ),
    ]

    response = generator.generate(
        query="What are the passing and attendance requirements?",
        chunks=chunks,
    )

    assert client.calls == 1
    assert "Question:What are the passing and attendance requirements?" in client.last_prompt
    assert "<context>" in client.last_prompt
    assert response.is_grounded is True
    assert response.cited_sources == [
        {"file_name": "bachelor.pdf", "page_number": 1},
        {"file_name": "bachelor.pdf", "page_number": 2},
    ]
    assert response.cited_pages == [1, 2]
    assert response.answer == fake_response
    assert response.raw_response == fake_response


def test_generate_multi_document_cross_citations():
    fake_response = (
        "Students can choose software majors [handbook.pdf • Page 3] "
        "and must maintain good academic standing [regulations.pdf • Page 7]."
    )
    client = FakeLLMClient(response_text=fake_response)
    generator = Generator(llm_client=client)

    chunks = [
        RetrievedChunk(text="Majors info", file_name="handbook.pdf", page_number=3),
        RetrievedChunk(text="Conduct policy", file_name="regulations.pdf", page_number=7),
    ]

    response = generator.generate(query="What are the rules and majors?", chunks=chunks)

    assert response.is_grounded is True
    assert response.cited_sources == [
        {"file_name": "handbook.pdf", "page_number": 3},
        {"file_name": "regulations.pdf", "page_number": 7},
    ]
    assert response.cited_pages == [3, 7]


def test_generate_deduplicates_and_sorts_citations():
    fake_response = (
        "Important topics are discussed in [doc.pdf • Page 5], referenced earlier in [doc.pdf • Page 2], "
        "and reviewed again in [doc.pdf • Page 5] and [doc.pdf • Page 1]."
    )
    client = FakeLLMClient(response_text=fake_response)
    generator = Generator(llm_client=client)

    chunks = [
        RetrievedChunk(text="Sample content", file_name="doc.pdf", page_number=1)
    ]

    response = generator.generate(query="Where are the topics discussed?", chunks=chunks)

    assert response.is_grounded is True
    assert response.cited_sources == [
        {"file_name": "doc.pdf", "page_number": 1},
        {"file_name": "doc.pdf", "page_number": 2},
        {"file_name": "doc.pdf", "page_number": 5},
    ]
    assert response.cited_pages == [1, 2, 5]


def test_generate_legacy_single_doc_citation_fallback():
    """If LLM outputs legacy [Page X] format with single-file context, it attributes to that file."""
    fake_response = "Software engineering is foundational [Page 3]."
    client = FakeLLMClient(response_text=fake_response)
    generator = Generator(llm_client=client)

    chunks = [
        RetrievedChunk(text="Foundational SE course", file_name="syllabus.pdf", page_number=3)
    ]

    response = generator.generate(query="What is foundational?", chunks=chunks)

    assert response.is_grounded is True
    assert response.cited_sources == [{"file_name": "syllabus.pdf", "page_number": 3}]
    assert response.cited_pages == [3]


def test_generate_handles_fallback_message():
    client = FakeLLMClient(response_text=Generator.FALLBACK_MESSAGE)
    generator = Generator(llm_client=client)

    chunks = [
        RetrievedChunk(text="Irrelevant content", file_name="doc.pdf", page_number=1)
    ]

    response = generator.generate(query="What is the tuition fee?", chunks=chunks)

    assert response.is_grounded is False
    assert response.cited_sources == []
    assert response.cited_pages == []
    assert response.answer == Generator.FALLBACK_MESSAGE


def test_generate_fast_fails_on_empty_chunks_without_calling_llm():
    client = FakeLLMClient(response_text="Should never be called")
    generator = Generator(llm_client=client)

    response = generator.generate(query="Any question", chunks=[])

    assert client.calls == 0
    assert response.is_grounded is False
    assert response.cited_sources == []
    assert response.cited_pages == []
    assert response.answer == Generator.FALLBACK_MESSAGE
