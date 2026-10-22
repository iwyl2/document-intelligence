from document_intelligence.services.rag_service import RagService
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from document_intelligence.api.errors import register_exception_handlers
from document_intelligence.api.routes import router
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan context manager.
    Runs startup tasks before receiving requests, and cleanup tasks upon shutdown.
    """
    print("Initialize the rag service")
    app.state.rag_service = RagService.create_default()
    print("Rag service initialization success")

    yield

    print("Shutting down Document Intelligence API...")


app = FastAPI(
    title="Document Intelligence API",
    description="RAG-powered Document Intelligence engine with grounded answers and inline citations.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(router)


@app.get("/health", tags=["Health"])
def health_check():
    """Verify that the API server is up and responsive."""
    return {"status": "ok", "service": "document-intelligence-api"}
