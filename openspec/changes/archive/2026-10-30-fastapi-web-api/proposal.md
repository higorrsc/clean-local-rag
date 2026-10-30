# Proposal: FastAPI Async Web API and Batch Ingestion

## Why

While the Typer CLI enables local terminal-based interaction, exposing the RAG pipeline through an asynchronous FastAPI Web API allows users to interact with the system via web clients and browsers. Additionally, providing automated batch ingestion by language folder enables quick initialization of the knowledge base without manually passing individual files.

## What Changes

- **FastAPI Dependency**: Add `fastapi[standard]` and `uvicorn[standard]` to dependencies in `pyproject.toml`.
- **Async Adapters and Use Cases**: Introduce async support across adapters and application use cases (`AsyncEmbeddingGateway`, `AsyncLLMGateway`, `AsyncVectorRepository`) using `httpx.AsyncClient`.
- **Language Directory Batch Ingestion**: Extend document ingestion with a batch ingestion use case and endpoint that takes a target language identifier (e.g. `pt-br` or `en`) and ingests all markdown documents located in `docs/<language>/`.
- **Spec-Driven Contracts**: Update `openapi.yaml` to include the language batch ingestion endpoint (`/documents/ingest/by-language`), health check (`/health`), and generate updated Pydantic models.
- **FastAPI Web Presentation Layer**: Implement the FastAPI application in `src/api/` using best practices (`Annotated` dependencies, `APIRouter`, lifespan management, interactive web interface or static UI serving).
- **Test Suite**: Add async unit and integration tests using `httpx.AsyncClient` and `fastapi.testclient.TestClient`.

## Capabilities

### New Capabilities

- `web-api`: Provides an asynchronous HTTP REST and interactive web interface to execute document ingestion, health monitoring, and semantic query operations.

### Modified Capabilities

- `document-ingestion`: Adding requirement for batch directory ingestion by language folder (`docs/<language>`), parsing and indexing all documents within the specified language directory.

## Impact

- **Dependencies**: Adds `fastapi>=0.115.0` and `uvicorn>=0.30.0`.
- **Application & Adapters**: Adds async execution pathways to preserve Clean Architecture without blocking the event loop.
- **Contract**: Extends `openapi.yaml` with language batch ingestion and health routes.
- **Presentation**: Introduces `src/api/` alongside existing `src/cli/`.
