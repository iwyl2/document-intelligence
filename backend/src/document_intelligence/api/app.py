import os
from contextlib import asynccontextmanager
from document_intelligence.api.workspace_routes import router as workspace_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from document_intelligence.api.errors import register_exception_handlers
from document_intelligence.api.routes import router
from document_intelligence.api.auth_routes import router as auth_router
from document_intelligence.db.models import Base
from document_intelligence.db.session import engine
from document_intelligence.services.rag_service import RagService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan context manager.
    Runs startup tasks before receiving requests, and cleanup tasks upon shutdown.
    """
    print("Verifying database schema...")
    Base.metadata.create_all(bind=engine)
    print("Database schema verified.")

    print("Initialize the rag service")
    app.state.rag_service = RagService.create_default()
    print("Rag service initialization success")

    yield

    print("Shutting down Document Intelligence API...")


app = FastAPI(
    title="Document Intelligence API",
    description="RAG-powered Document Intelligence engine with grounded answers and inline citations.",
    version="2.0.0",
    lifespan=lifespan,
)

allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins_raw == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(router)
app.include_router(auth_router)
app.include_router(workspace_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Verify that the API server is up and responsive."""
    return {"status": "ok", "service": "document-intelligence-api"}
