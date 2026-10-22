# Document Intelligence

**Grounded Retrieval-Augmented Generation (RAG) engine with strict page-level citation attribution and deterministic hallucination fallback.**

![Python 3.13](https://img.shields.io/badge/python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)
![Package Manager](https://img.shields.io/badge/managed%20by-uv-DE5FE9?style=flat-square)
![Frontend](https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js)
![Vector DB](https://img.shields.io/badge/storage-ChromaDB-orange?style=flat-square)
![Tests](https://img.shields.io/badge/tests-26%20passed%20%7C%20100%25-brightgreen?style=flat-square)

---

## Overview

Most traditional RAG pipelines fail in high-stakes environments because they hallucinate unsupported facts, lose document context boundaries, or provide unverified answers without auditable provenance.

**Document Intelligence** is an engineering-first RAG implementation designed to solve document attribution from the ground up:
- **No Hallucinations**: If retrieved context does not answer the question, the system produces a deterministic fallback message rather than speculating.
- **Page-Level Grounding**: Every factual assertion is mapped directly to source page numbers (`[Page X]`).
- **Semantic Boundary Chunking**: Splits documents at points of topical shift by measuring cosine similarity drops between adjacent sentence vectors, avoiding arbitrary character or token cutoffs.
- **100% Local Dense Embeddings**: Generates 384-dimensional dense vectors using `all-MiniLM-L6-v2` locally on CPU without third-party embedding API costs.

---

## System Architecture

The core pipeline processes unstructured text documents through five discrete, verifiable layers:

```
[ PDF Document ]
       │
       ▼
1. INGESTION LAYER            -> pypdf extraction (1-based page indexing)
       │
       ▼
2. NORMALIZATION LAYER        -> Unicode NFKC normalization, whitespace & paragraph cleanup
       │
       ▼
3. SEMANTIC CHUNKING LAYER    -> Adjacent sentence cosine similarity & drop detection (80th percentile)
       │
       ▼
4. VECTOR INDEXING LAYER      -> 384-dim dense embeddings (all-MiniLM-L6-v2) indexed into ChromaDB
       │
       ▼
5. GROUNDED GENERATION LAYER  -> XML context injection, prompt grounding, inline regex citation extraction
```

### 1. Ingestion (`backend/src/document_intelligence/ingestion/`)
Extracts text page-by-page from text-based PDFs while strictly enforcing 1-based index integrity (`DocumentPage.page_number >= 1`) across all downstream representations.

### 2. Normalization (`backend/src/document_intelligence/processing/text.py`)
Cleans text through Unicode NFKC normalization, strips carriage returns (`\r\n` to `\n`), condenses multi-space sequences, and preserves semantic paragraph divisions (`\n\n`).

### 3. Semantic Chunking (`backend/src/document_intelligence/processing/semantic_chunker.py`)
Instead of naive fixed-size chunking, the chunker computes cosine similarity between adjacent sentence vectors:
$$\text{Sim}(u, v) = \frac{u \cdot v}{\|u\|_2 \|v\|_2}$$
It measures similarity drops ($\text{Sim}_i - \text{Sim}_{i+1}$) and places chunk boundaries at drops exceeding the 80th percentile threshold, keeping coherent topics grouped together.

### 4. Vector Storage (`backend/src/document_intelligence/storage/vector_storage.py`)
Indexes chunks with deterministic IDs (`{file_name}-page-{page_no}-chunk-{index}`) and explicit metadata (`file_name`, `page_number`) in ChromaDB.

### 5. Grounded Generation (`backend/src/document_intelligence/generation/generator.py`)
Formats retrieved context into XML structure (`<context><chunk page="X">...</chunk></context>`). The generator prompts the LLM under strict grounding constraints, extracts cited pages via regex (`r"\[Page\s+(\d+)\]"`), and verifies that answers are fully supported by the document.

---

## Empirical Evaluation Benchmarks

The retrieval and ranking pipeline is evaluated using Information Retrieval (IR) metrics against synthetic multi-query fixtures (`backend/tests/evaluation/`):

| Evaluation Metric | Target Threshold | Measured Score | Evaluation Purpose |
| :--- | :--- | :--- | :--- |
| **Recall@1** | $\ge 0.60$ | **0.67** | Frequency at which the relevant context chunk is ranked at Rank #1. |
| **Recall@3** | $\ge 0.80$ | **0.83** | Probability that the target context is within the top-3 retrieved candidates. |
| **Recall@5** | $1.00$ | **1.00** | Guarantees the target context is captured in the top-5 candidates (100% recall). |
| **MRR** | $\ge 0.75$ | **0.83** | Mean Reciprocal Rank quantifying context retrieval ordering quality. |

---

## Repository Layout

The project is structured as an independent monorepo with decoupled backend and frontend engines:

```text
document-intelligence/
├── AGENTS.md                          # Architectural governance and review runbooks
├── docs/
│   ├── scope.md                       # System specification & mathematical definitions
│   └── logs.md                        # Architecture log
├── backend/                           # Python Engine (managed via uv)
│   ├── pyproject.toml                 # uv manifest (ChromaDB, FastAPI, PyTorch, PyPDF)
│   ├── uv.lock                        # Deterministic dependency lockfile
│   ├── Dockerfile                     # Production container image definition
│   ├── src/document_intelligence/
│   │   ├── __init__.py                # CLI runner
│   │   ├── exceptions.py              # Domain exceptions (DocumentNotFoundError, etc.)
│   │   ├── models/                    # Typed dataclasses (Document, Chunk, GenerationResponse)
│   │   ├── ingestion/                 # Layer 1: PDF extraction
│   │   ├── processing/                # Layer 2 & 3: Normalization, chunking, embeddings
│   │   ├── storage/                   # Layer 4: ChromaDB vector storage
│   │   ├── retrieval/                 # Semantic search & ranking
│   │   ├── generation/                # Layer 5: Grounded generation & LLM adapters
│   │   ├── services/                  # Application service layer (RagService)
│   │   └── api/                       # FastAPI REST API (endpoints, schemas, error handlers)
│   └── tests/                         # Automated test suite (26 unit/integration/eval tests)
└── frontend/                          # Web UI Application (Next.js 16 + Tailwind CSS)
    ├── src/app/page.tsx               # Product overview & architecture showcase
    ├── src/app/workspace/page.tsx     # Split-screen workbench (PDF upload + citation chat)
    ├── src/components/                # Navbar, LoginModal, and UI components
    └── src/lib/api.ts                 # Strongly-typed backend API client
```

---

## Getting Started

### Prerequisites
- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)** (modern Python package manager)
- **Node.js 20+** and **npm**

---

### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a local `.env` file with your LLM provider credentials:
   ```env
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

3. Install dependencies and run the automated test suite:
   ```bash
   uv run pytest -v
   ```

4. Start the FastAPI development server:
   ```bash
   uv run uvicorn document_intelligence.api.app:app --reload --port 8000
   ```
   Interactive Swagger documentation will be available at `http://localhost:8000/docs`.

---

### 2. Frontend Setup

1. In a new terminal, navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Next.js development server:
   ```bash
   npm run dev
   ```

4. Open `http://localhost:3000` in your browser.
   - Enter your workspace passcode (configured via `NEXT_PUBLIC_WORKSPACE_PASSCODE`, default: `doc-intel-2026`).
   - Drag and drop a PDF file into the ingestion dropzone.
   - Submit queries and view answers rendered with inline `[Page X]` citation pills.

---

### 3. CLI Direct Execution

You can also run the complete ingestion-to-answer pipeline directly via CLI without running the web server:

```bash
uv run --directory backend document-intelligence
```

---

## API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Health check endpoint returning API availability status. |
| `POST` | `/api/v1/documents/upload` | Uploads and indexes a PDF document into ChromaDB. |
| `GET` | `/api/v1/documents/status` | Returns chunk count and file names in the active in-memory index. |
| `DELETE` | `/api/v1/documents` | Atomically clears all indexed documents from the in-memory vector store. |
| `POST` | `/api/v1/query` | Executes semantic retrieval and returns a grounded answer with cited page numbers. |

---

## License

This project is licensed under the MIT License.
