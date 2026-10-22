from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from document_intelligence.exceptions import DocumentNotFoundError, DocumentReadError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DocumentNotFoundError)
    async def document_not_found_handler(req: Request, exc: DocumentNotFoundError):
        return JSONResponse(
            status_code=404,
            content={
                "detail": str(exc),
                "error_type": "DocumentNotFoundError",
            },
        )

    @app.exception_handler(DocumentReadError)
    async def document_read_error_handler(request: Request, exc: DocumentReadError):
        return JSONResponse(
            status_code=422,
            content={
                "detail": str(exc),
                "error_type": "DocumentReadError",
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=400,
            content={
                "detail": str(exc),
                "error_type": "ValueError",
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An internal server error occurred.",
                "error_type": "InternalServerError",
            },
        )
