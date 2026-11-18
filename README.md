# Document Intelligence

**Cloud-Ready, Multi-Tenant Retrieval-Augmented Generation (RAG) Engine with Cross-Document Attribution, Semantic Chunking, and Deterministic Fallback.**

![Version](https://img.shields.io/badge/version-2.0.0-blue?style=flat-square)
![Python 3.13](https://img.shields.io/badge/python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)
![Package Manager](https://img.shields.io/badge/managed%20by-uv-DE5FE9?style=flat-square)
![Frontend](https://img.shields.io/badge/Next.js-16.4.6-black?style=flat-square&logo=next.js)
![Vector DB](https://img.shields.io/badge/storage-ChromaDB-orange?style=flat-square)
![Control Plane](https://img.shields.io/badge/control--plane-PostgreSQL%20%7C%20SQLite-blue?style=flat-square)
![Tests](https://img.shields.io/badge/tests-67%20passed%20%7C%20100%25-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

---

## Overview

Most traditional RAG implementations fail in real-world production environments because they suffer from four fundamental flaws:

1. **Hallucination Under Uncertainty**: Speculating answers when documents lack the necessary facts.
2. **Loss of Provenance**: Summarizing context without verifiable file and page citations.
3. **Arbitrary Chunk Boundaries**: Slicing documents into fixed character counts, splitting coherent concepts mid-sentence.
4. **Heavy Container Footprints**: Forcing heavy PyTorch and transformer weights (~900 MB RAM) into cloud containers, causing serverless `OOMKilled` crashes.

**Document Intelligence v2.0** is an engineering-first, multi-tenant RAG platform designed to solve these challenges from the ground up:

- **Zero-Speculation Fallback**: Produces a deterministic fallback response when retrieved context is insufficient, preventing synthetic hallucination.
- **Cross-Document Corpus Grounding**: Every claim is strictly attributed to source files and page numbers (`[file_name • Page X]`).
- **Semantic Boundary Chunking**: Places chunk boundaries at topical transition points by evaluating adjacent-sentence cosine distance drops exceeding the 80th percentile threshold.
- **Pluggable Embedding Architecture**: An abstract `BaseEmbedder` protocol supporting both local PyTorch CPU embeddings (`all-MiniLM-L6-v2`) and ultra-lightweight cloud REST embeddings (`gemini-embedding-001`, **< 60 MB RAM**), enabling scale-to-zero serverless hosting.
- **Multi-Tenant Workspace Sessions**: Users create and manage isolated workspaces. Dense vector collections and relational records are partitioned strictly by session ID.
- **Dual-Plane Synchronization**: Document and workspace deletions execute atomic dual-plane purges across both dense vector storage (ChromaDB) and relational tables (Neon PostgreSQL / SQLite).
- **Secure Control Plane**: Built on modern SQLAlchemy 2.0 with bcrypt hashing, JWT authentication, and administrative user approval gating.

---

## System Architecture

```text
[ Academic / Technical PDFs ]
             │
             ▼
   1. INGESTION LAYER            -> pypdf extraction (Strict 1-based page indexing)
             │
             ▼
   2. NORMALIZATION LAYER        -> Unicode NFKC normalization, whitespace & paragraph preservation
             │
             ▼
   3. SEMANTIC CHUNKING LAYER    -> Sentence cosine similarity drops (80th percentile threshold)
             │
             ▼
   4. PLUGGABLE EMBEDDING LAYER  -> BaseEmbedder (Local SentenceTransformer vs. Cloud Gemini REST <60MB)
             │
             ▼
   5. VECTOR STORAGE LAYER       -> Session-partitioned collections (ChromaDB)
             │
             ▼
   6. GROUNDED GENERATION LAYER  -> XML context blocks, strict prompts, regex cross-doc citations
             │
             ▼
   7. RELATIONAL CONTROL PLANE   -> PostgreSQL / SQLite (Users, JWT, Workspaces, Document Records)
```

### 1. Ingestion (`backend/src/document_intelligence/ingestion/`)

Extracts text page-by-page from digital PDFs while strictly enforcing 1-based indexing (`DocumentPage.page_number >= 1`) across all downstream representations.

### 2. Normalization (`backend/src/document_intelligence/processing/text.py`)

Cleans text through Unicode NFKC normalization, converts `\r\n` to `\n`, condenses multi-space sequences, and preserves semantic paragraph divisions (`\n\n`).

### 3. Semantic Chunking (`backend/src/document_intelligence/processing/semantic_chunker.py`)

Instead of fixed token lengths, adjacent sentence vectors are compared via cosine similarity:

$$
\text{Sim}(u, v) = \frac{u \cdot v}{\|u\|_2 \|v\|_2}
$$

Chunk boundaries are created whenever similarity drops ($\text{Sim}_i - \text{Sim}_{i+1}$) exceed the 80th percentile, keeping related topical statements intact.

### 4. Pluggable Embeddings (`backend/src/document_intelligence/processing/embedder.py`)

Decoupled behind an abstract `BaseEmbedder` interface:

- **`LocalEmbedder`**: 384-dimensional dense vectors via PyTorch `all-MiniLM-L6-v2` locally on CPU.
- **`CloudEmbedder`**: Generates 384-dimensional embeddings via Google Gemini REST API (<60MB RAM footprint). Auto-selected when `GEMINI_API_KEY` is present.

### 5. Vector Storage & Isolation (`backend/src/document_intelligence/storage/vector_storage.py`)

Manages session-partitioned collections in ChromaDB. Each workspace gets its own deterministic collection (`session_{workspace_id}`). Supports single-document chunk deletion by metadata filter (`where={"file_name": file_name}`).

### 6. Grounded Generation (`backend/src/document_intelligence/generation/generator.py`)

Formats retrieved context into XML structure:

```xml
<context>
  <chunk file="syllabus.pdf" page="1">...</chunk>
  <chunk file="regulations.pdf" page="4">...</chunk>
</context>
```

Extracts cited sources via regex (`r"\[([^•\]]+?)\s*•\s*[Pp]age\s*(\d+)\]"`), automatically deduplicates and sorts citations, and verifies grounding before returning.

### 7. Relational Control Plane (`backend/src/document_intelligence/db/`, `auth/`)

SQLAlchemy 2.0 models manage `User`, `WorkspaceSession`, and `DocumentRecord`. Auto-bootstraps the initial user as an active administrator; subsequent registrations require admin activation.

---

## Empirical Evaluation Benchmarks

The retrieval pipeline is evaluated against Information Retrieval (IR) metrics using synthetic multi-query fixtures (`backend/tests/evaluation/`):

| Evaluation Metric | Target Threshold | Measured Score | Evaluation Purpose |
| :--- | :--- | :--- | :--- |
| **Recall@1** | $\ge 0.60$ | **0.67** | Frequency at which the most relevant chunk is ranked at Rank #1. |
| **Recall@3** | $\ge 0.80$ | **0.83** | Probability that target context is captured within the top-3 candidates. |
| **Recall@5** | $1.00$ | **1.00** | Guarantees target context is captured within top-5 candidates (**100% recall**). |
| **MRR** | $\ge 0.75$ | **0.83** | Mean Reciprocal Rank evaluating search ordering quality. |

---

## Repository Layout

```text
document-intelligence/
├── AGENTS.md                          # Architectural governance, roles, and review runbooks
├── docs/
│   ├── scope.md                       # V1 Baseline specification
│   ├── v2_scope.md                    # V2 Cloud-Ready Multi-Tenant specification
│   └── logs.md                        # Architecture log
├── backend/                           # Python Engine (managed via uv)
│   ├── pyproject.toml                 # uv manifest (FastAPI, SQLAlchemy, ChromaDB, PyPDF)
│   ├── uv.lock                        # Deterministic dependency lockfile
│   ├── Dockerfile                     # Production container image definition
│   ├── main.py                        # Entrypoint for FastAPI CLI / Cloud
│   ├── src/document_intelligence/
│   │   ├── __init__.py                # Package entrypoint
│   │   ├── exceptions.py              # Domain exceptions (DocumentNotFoundError, etc.)
│   │   ├── models/                    # Typed dataclasses (Document, Chunk, GenerationResponse)
│   │   ├── ingestion/                 # Layer 1: PDF extraction
│   │   ├── processing/                # Layer 2 & 3: Normalization, chunking, embeddings
│   │   ├── storage/                   # Layer 4: Session-partitioned vector storage
│   │   ├── retrieval/                 # Semantic search & ranking
│   │   ├── generation/                # Layer 5: Grounded generation & LLM adapters
│   │   ├── services/                  # Application service layer (RagService)
│   │   ├── auth/                      # JWT token generation, security, and dependencies
│   │   ├── db/                        # SQLAlchemy 2.0 models, session, and migrations
│   │   └── api/                       # FastAPI routes, schemas, and error handlers
│   └── tests/                         # Automated test suite (67 unit/integration/eval tests)
└── frontend/                          # Web UI Application (Next.js 16.4.6 + React 19 + Tailwind CSS)
    ├── src/app/page.tsx               # Product overview & architecture showcase
    ├── src/app/workspace/page.tsx     # Multi-tenant workbench (Upload, Document list, Chat)
    ├── src/components/                # Navbar, LoginModal, and citation components
    ├── src/context/AuthContext.tsx    # JWT Authentication context & state rehydration
    └── src/lib/api.ts                 # Strongly-typed backend API client with dual-plane headers
```

---

## Getting Started

### Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)** (modern, deterministic Python package manager)
- **Node.js 20+** and **npm**

---

### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a local `.env` file:
   ```env
   # LLM Generation (OpenRouter / OpenAI)
   OPENROUTER_API_KEY=your_openrouter_api_key_here

   # Embeddings: 'local' (PyTorch CPU) or 'cloud' (Google Gemini REST API <60MB RAM)
   EMBEDDER_BACKEND=local
   GEMINI_API_KEY=your_gemini_api_key_here

   # Control Plane Database (PostgreSQL or local SQLite)
   DATABASE_URL=sqlite:///./data/control_plane.db

   # Security
   JWT_SECRET=your_super_secret_jwt_key_here
   JWT_EXPIRE_MINUTES=60
   ```

3. Install dependencies and run the complete test suite:
   ```bash
   uv sync
   uv run pytest -v
   ```

4. Start the FastAPI development server:
   ```bash
   uv run uvicorn document_intelligence.api.app:app --reload --port 8000
   ```
   Interactive Swagger documentation is available at `http://localhost:8000/docs`.

---

### 2. Frontend Setup

1. In a new terminal, navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Configure environment variables in `frontend/.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. Install dependencies and start the development server:
   ```bash
   npm install
   npm run dev
   ```

4. Open `http://localhost:3000` in your browser:
   - Click **Sign In / Register** to create an account (the first registered account automatically becomes the Active Admin).
   - Create or select an isolated **Workspace Session**.
   - Drag and drop PDF files into the ingestion dropzone.
   - Query documents and view grounded answers with interactive `[file_name • Page X]` citation badges.

---

### 3. CLI Direct Pipeline Execution

Run the complete extraction → chunking → embedding → query pipeline directly via CLI:

```bash
uv run --directory backend document-intelligence
```

---

## Production Cloud Deployment

### Backend (FastAPI Cloud)

The backend is optimized for zero-config serverless deployment on **[FastAPI Cloud](https://fastapicloud.com)**:

```bash
# 1. Login to FastAPI Cloud
uv run --directory backend fastapi login

# 2. Deploy
uv run --directory backend fastapi deploy
```

Set `EMBEDDER_BACKEND=cloud`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, and a managed serverless Postgres URL (`DATABASE_URL`, e.g., from [Neon.tech](https://neon.tech)) in your FastAPI Cloud environment dashboard.

### Frontend (Vercel)

Deploy the Next.js frontend to **[Vercel](https://vercel.com)**:

- Set environment variable: `NEXT_PUBLIC_API_URL=https://your-app.fastapicloud.dev` (Type: **Config**)
- Push to `main` branch to trigger automated Turbopack builds.

---

## API Reference

### Health & Core Ingestion

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Health check endpoint returning API availability status. |
| `POST` | `/api/v1/documents/upload` | Uploads, chunks, embeds, and indexes a PDF document into workspace session. |
| `GET` | `/api/v1/documents/status` | Returns chunk count and indexed file names for the active workspace. |
| `DELETE` | `/api/v1/documents` | Dual-plane purge: clears both vector chunks and relational metadata for the workspace. |
| `DELETE` | `/api/v1/documents/{id}` | Deletes a specific document record and all its associated vector chunks. |
| `POST` | `/api/v1/query` | Executes semantic retrieval and returns grounded answer with structured citations. |

### Auth & User Management (Control Plane)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Registers new user account (auto-bootstraps first user as active admin). |
| `POST` | `/api/v1/auth/login` | Authenticates credentials and returns JWT bearer token. |
| `GET` | `/api/v1/auth/me` | Returns current authenticated user profile and admin status. |
| `GET` | `/api/v1/auth/users` | Admin-only endpoint listing all system users. |
| `PATCH` | `/api/v1/auth/users/{id}/status` | Admin-only endpoint to activate or deactivate user accounts. |

### Workspaces & Multi-Tenancy

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/workspaces/` | Lists all workspaces owned by the authenticated user with nested document counts. |
| `POST` | `/api/v1/workspaces/` | Creates a new named workspace session for isolated document management. |
| `GET` | `/api/v1/workspaces/{id}` | Retrieves workspace details, ownership verification, and document records. |
| `DELETE` | `/api/v1/workspaces/{id}` | Dual-plane cascade deletion: purges ChromaDB vector collection and database records. |

---

## Future Roadmap & Planned Improvements

- [ ] **Pluggable Cloud Vector Storage (Pinecone Integration)**:
  Implement an optional `PineconeStorage` adapter using Pinecone Serverless with tenant-isolated namespaces (`namespace=session_{id}`), enabling external persistent cloud vector storage without in-container RAM overhead.
- [ ] **Automated RAG Triad Evaluations (`tests/evaluation/test_rag_triad.py`)**:
  Expand quantitative metrics to evaluate generation quality:
  - **Faithfulness / Groundedness** ($\ge 0.90$): Ratio of factual assertions grounded in retrieved context.
  - **Answer Relevance** ($\ge 0.85$): Semantic similarity between user query and generated response.
  - **Context Precision**: Signal-to-noise ratio of ranked context chunks.
- [ ] **Hybrid Search (BM25 Sparse + Dense Vectors)**:
  Combine exact keyword lexical retrieval (BM25) with dense semantic embeddings via Reciprocal Rank Fusion (RRF) for enhanced acronym and technical term recall.
- [ ] **Async PDF Processing & Streaming**:
  Support large multi-page PDFs (100+ pages) with asynchronous background task processing and real-time chunking progress streaming via WebSockets.
- [ ] **Semantic Caching**:
  Cache dense query vectors and grounded answers in an in-memory key-value cache to reduce repetitive LLM and embedding API costs.

---

## License

This project is licensed under the MIT License.
