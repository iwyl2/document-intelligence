# Document Intelligence — Backend Engine

**High-performance Python RAG engine featuring local dense embeddings, cosine-drop semantic chunking, and grounded citation generation.**

![Python 3.13](https://img.shields.io/badge/python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)
![Package Manager](https://img.shields.io/badge/managed%20by-uv-DE5FE9?style=flat-square)
![Framework](https://img.shields.io/badge/FastAPI-0.159-009688?style=flat-square&logo=fastapi&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-1.5.9-orange?style=flat-square)
![Tests](https://img.shields.io/badge/tests-26%20passed%20%7C%20100%25-brightgreen?style=flat-square)

---

## Architectural Layout

The backend package is structured under `src/document_intelligence/` following Clean Architecture:

```text
backend/
├── pyproject.toml                     # uv manifest & dependencies
├── uv.lock                            # Deterministic lockfile
├── Dockerfile                         # Production container image
├── src/document_intelligence/
│   ├── __init__.py                    # Standalone CLI entrypoint
│   ├── exceptions.py                  # Domain exceptions (DocumentNotFoundError, etc.)
│   ├── models/                        # Domain Data Transfer Objects (dataclasses)
│   │   ├── document.py                # Document, DocumentPage
│   │   ├── chunk.py                   # Chunk, EmbeddedChunk
│   │   ├── retriever.py               # RetrievedChunk
│   │   ├── generation.py              # GenerationResponse
│   │   └── service.py                 # IngestionResult
│   ├── ingestion/                     # Layer 1: PDF text extraction (pypdf)
│   ├── processing/                    # Layer 2 & 3: Normalization, chunking, embeddings
│   │   ├── text.py                    # clean_text (NFKC, whitespace, lines)
│   │   ├── document.py                # clean_document (page-by-page pipeline)
│   │   ├── embedder.py                # SentenceTransformer (all-MiniLM-L6-v2, 384 dims)
│   │   └── semantic_chunker.py        # Cosine distance drop detector (80th percentile)
│   ├── storage/                       # Layer 4: Vector database abstraction
│   │   └── vector_storage.py          # ChromaDB collection & indexing engine
│   ├── retrieval/                     # Semantic search & dense query retrieval
│   │   └── retriever.py               # Top-k vector ranking
│   ├── generation/                    # Layer 5: Grounded generation & citations
│   │   ├── generator.py               # XML context formatting & prompt grounding
│   │   └── adapters.py                # LLM client adapters (OpenRouter / OpenAI)
│   ├── services/                      # Application Service Layer
│   │   └── rag_service.py             # RagService (Dependency Injection & lifecycle root)
│   └── api/                           # Web API Layer
│       ├── app.py                     # FastAPI application & lifespan management
│       ├── routes.py                  # REST endpoints (/upload, /status, /query, DELETE)
│       ├── schemas.py                 # Pydantic request & response schemas
│       └── errors.py                  # Domain exception to HTTP status code mappings
└── tests/                             # Automated test suite (26 unit, integration, eval tests)
```

---

## Environment Setup

### 1. Requirements
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

### 2. Configuration
Create a local `.env` file inside `backend/`:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 3. Installation
Install all production and development dependencies deterministically:

```bash
uv sync
```

---

## Development & Execution

### Run the FastAPI Web Server
```bash
uv run uvicorn document_intelligence.api.app:app --reload --port 8000
```
- Swagger UI Documentation: `http://localhost:8000/docs`
- OpenAPI JSON Schema: `http://localhost:8000/openapi.json`

### Run Standalone CLI Pipeline
Directly test ingestion, chunking, retrieval, and live generation on sample fixtures:
```bash
uv run document-intelligence
```

### Run Automated Test Suite
Execute the entire test suite across all 5 architectural layers and IR evaluation metrics:
```bash
uv run pytest -v
```

---

## REST API Reference

| Method | Endpoint | Description | Request Payload | Response |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | Health check | None | `{"status": "ok"}` |
| `POST` | `/api/v1/documents/upload` | Upload & index PDF | `multipart/form-data` (`file`) | `UploadResponse` (`file_name`, `num_pages`, `num_chunks`) |
| `GET` | `/api/v1/documents/status` | In-memory index status | None | `{"total_chunks": int, "indexed_files": list, "is_empty": bool}` |
| `DELETE` | `/api/v1/documents` | Purge in-memory index | None | `{"message": str, "total_chunks": 0}` |
| `POST` | `/api/v1/query` | Grounded question answering | `{"question": str, "top_k": int}` | `QueryResponse` (`answer`, `cited_pages`, `is_grounded`) |

---

## Containerization

A multi-stage production container image is defined in [`Dockerfile`](file:///d:/Projects/document-intelligence/backend/Dockerfile):

```bash
# Build Docker image
docker build -t document-intelligence-backend .

# Run container
docker run -p 8000:8000 -e OPENROUTER_API_KEY="your-key" document-intelligence-backend
```
