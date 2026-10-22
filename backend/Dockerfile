# Use official Python slim image
FROM python:3.13-slim

# Install uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Optimize uv performance
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONUNBUFFERED=1

# Copy dependency manifests first for layer caching
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy backend source code
COPY src ./src

# Install package
RUN uv sync --frozen --no-dev

# Add virtualenv to PATH
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Start Uvicorn server bound to 0.0.0.0
CMD ["uvicorn", "document_intelligence.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
