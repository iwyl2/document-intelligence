from datetime import datetime
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Payload for asking a question against indexed documents."""

    question: str = Field(
        ...,
        min_length=1,
        description="The question to ask against the indexed documents.",
        examples=["What practical experience do students get in the program?"],
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of top chunks to retrieve for context (between 1 and 10).",
        examples=[3],
    )


class QueryResponse(BaseModel):
    """Response returned after semantic retrieval and grounded generation."""

    answer: str = Field(
        ...,
        description="The grounded answer with inline citations.",
    )
    cited_pages: list[int] = Field(
        default_factory=list,
        description="List of 1-based page numbers cited in the answer.",
        examples=[[1, 2]],
    )
    is_grounded: bool = Field(
        ...,
        description="True if the response is grounded in the document; False if fallback occurred.",
    )


class UploadResponse(BaseModel):
    """Response returned when a PDF is parsed, chunked, and indexed."""

    file_name: str = Field(..., description="Name of the uploaded PDF file.")
    num_pages: int = Field(..., description="Total pages extracted from the PDF.")
    num_chunks: int = Field(
        ..., description="Total semantic chunks indexed in ChromaDB."
    )
    message: str = Field(
        default="Document successfully indexed.",
        description="Summary status message.",
    )


class ErrorResponse(BaseModel):
    """Standardized error payload returned across all endpoints."""

    detail: str = Field(..., description="Human-readable error explanation.")
    error_type: str = Field(
        ..., description="The classification or class name of the error."
    )


class UserRegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User plain password")


class UserLoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User plain password")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserStatusUpdateRequest(BaseModel):
    is_active: bool = Field(..., description="New active status for the user")
