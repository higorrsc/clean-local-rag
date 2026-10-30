from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

import src.presentation.api.dependencies as deps
from src.presentation.api.routers import (
    documents_router,
    health_router,
    query_router,
)

STATIC_DIR = Path(__file__).parent / "static"
INDEX_HTML = (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Lifespan context manager for initialization and graceful shutdown."""
    yield
    # Cleanup Ollama async HTTP connections upon shutdown
    if deps._ollama_adapter is not None:
        await deps._ollama_adapter.aclose()


app = FastAPI(
    title="Local RAG API",
    version="0.1.0",
    description="Local RAG REST API and Interactive Web Interface.",
    lifespan=lifespan,
)

# Register routers
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(query_router)


@app.get("/", response_class=HTMLResponse)
async def serve_interactive_web_ui() -> HTMLResponse:
    """Serve the interactive local RAG browser chat interface."""
    return HTMLResponse(content=INDEX_HTML)
