---
name: doc-intel-auditor
description: Audit Document Intelligence codebase against docs/scope.md, docs/v2_scope.md, and AGENTS.md for correctness, NumPy vector efficiency, edge-case safety, and strict scope conformance without scope creep.
---

# Document Intelligence Code Auditor

This skill provides the operational audit runbook for the **Document Intelligence** project, representing the standards of a Senior Software Engineer (5–6 years experience).

---

## Step-by-Step Audit Workflow

### 1. Verify In-Scope Conformance
- Read [`docs/scope.md`](file:///d:/Projects/document-intelligence/docs/scope.md), [`docs/v2_scope.md`](file:///d:/Projects/document-intelligence/docs/v2_scope.md), and [`AGENTS.md`](file:///d:/Projects/document-intelligence/AGENTS.md).
- Ensure the code being audited strictly belongs to the in-scope components for the active branch:
  - **V1 Foundation**: Text-based PDF extraction (`pypdf`), text normalization (`clean_text` NFKC), semantic chunking (cosine similarity drop detection, 80th percentile), ChromaDB vector storage, vector similarity retrieval (`Retriever`), IR evaluation (`Recall@k`, `MRR`), and grounded generator with citations (`[Page X]`).
  - **V2 Additions (`v2-dev`)**: Pluggable `BaseEmbedder` protocol (`LocalEmbedder` & `CloudEmbedder`), session-isolated vector storage (`session_id`), multi-document attribution (`[file_name • Page X]`), and RAG Triad evaluations (Faithfulness, Answer Relevance).
- **Flag any out-of-scope creep immediately**:
  - OCR for scanned handwriting / images
  - Distributed message queues / Celery / Kafka
  - Heavy agentic frameworks (LangChain / CrewAI / AutoGen)

### 2. Verify Integrity & Type Correctness
- **Data Models**: Ensure usage of domain dataclasses in `src/document_intelligence/models/`:
  - [`Document`](file:///d:/Projects/document-intelligence/src/document_intelligence/models/document.py) & [`DocumentPage`](file:///d:/Projects/document-intelligence/src/document_intelligence/models/document.py)
  - [`Chunk`](file:///d:/Projects/document-intelligence/src/document_intelligence/models/chunk.py) & [`EmbeddedChunk`](file:///d:/Projects/document-intelligence/src/document_intelligence/models/chunk.py)
  - [`RetrievedChunk`](file:///d:/Projects/document-intelligence/src/document_intelligence/models/retriever.py)
- **Exception Boundaries**: Ensure domain exceptions from `src/document_intelligence/exceptions.py` are raised instead of leaking low-level errors:
  - [`DocumentNotFoundError`](file:///d:/Projects/document-intelligence/src/document_intelligence/exceptions.py) when path does not exist.
  - [`DocumentReadError`](file:///d:/Projects/document-intelligence/src/document_intelligence/exceptions.py) on parse or permission failure.
- **Page Numbering**: Verify that page numbers are consistently 1-indexed (`page_number >= 1`).

### 3. Verify Computational Efficiency & Vectorization
- **Vector Operations**: Verify cosine similarity uses NumPy vectorized operations:
  $$\text{sim} = \frac{u \cdot v}{\|u\| \|v\|}$$
  Check for division-by-zero guards if a vector norm is zero.
- **Batching**: Ensure chunks are embedded in batches rather than redundant serial model calls when possible.
- **Memory & Storage**: Check that ChromaDB queries pass vector representations efficiently and collections are queried with appropriate `top_k`.

### 4. Verify Robustness & Edge Cases
- Empty string or whitespace-only inputs.
- Single-sentence documents (should produce 1 chunk without boundary crashes).
- Corrupted or unreadable PDF streams.
- Missing answer cases (generator must fall back to `"I cannot find this information in the provided document"`).

### 5. Automated Verification
Run the relevant test suite for the component under review:
- PDF Ingestion: `uv run pytest tests/unit/test_pdf.py -v`
- Text Cleaning: `uv run pytest tests/unit/test_text.py tests/unit/test_document_processing.py -v`
- Embeddings: `uv run pytest tests/unit/test_embedder.py -v`
- Semantic Chunker: `uv run pytest tests/unit/test_chunker.py -v`
- Vector Storage: `uv run pytest tests/unit/test_vector_storage.py -v`
- Retriever: `uv run pytest tests/unit/test_retriever.py -v`
- End-to-End Pipeline: `uv run pytest tests/integration/ -v`
- IR Evaluation: `uv run pytest tests/evaluation/ -v`
