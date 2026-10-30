# Tasks

## 1. Dependencies and OpenAPI Contract Updates

- [x] 1.1 Add `fastapi>=0.115.0` and `uvicorn>=0.30.0` to dependencies and configure `[tool.fastapi]` entrypoint in `pyproject.toml`, verifying with `uv sync`.
- [x] 1.2 Update `openapi.yaml` with `/documents/ingest/by-language` and `/health` endpoints and schemas (`BatchIngestRequest`, `BatchIngestResponse`, `HealthResponse`), verifying schema validity with YAML parser.
- [x] 1.3 Re-generate Pydantic models in `src/domain/models/schemas.py` and update exports in `src/domain/models/__init__.py`, verifying by importing generated models in Python.

## 2. Asynchronous Domain Protocols and Infrastructure Adapters

- [x] 2.1 Define asynchronous protocol interfaces (`AsyncEmbeddingGateway`, `AsyncLLMGateway`, `AsyncVectorRepository`) in `src/domain/interfaces/`, verified with protocol unit tests.
- [x] 2.2 Add asynchronous methods (`agenerate_embedding`, `agenerate_embeddings`, `agenerate_response`) to `OllamaAdapter` in `src/infra/adapters/ollama.py` using `httpx.AsyncClient`, verified with async unit tests using mocked HTTP transport.
- [x] 2.3 Add asynchronous methods (`asave_chunks`, `asearch_similar`) to `InMemoryVectorAdapter` in `src/infra/adapters/in_memory_repository.py`, verified with unit tests.

## 3. Asynchronous Application Use Cases

- [x] 3.1 Implement `AsyncBatchIngestByLanguageUseCase` in `src/application/use_cases/batch_ingest_language.py` scanning `docs/<language>/*.md` and ingesting chunks asynchronously, verified with unit tests.
- [x] 3.2 Add asynchronous execution (`aexecute`) to `IngestDocumentsUseCase` and `AskQuestionUseCase`, verified with unit tests using mock async gateways.

## 4. FastAPI Presentation Layer and Interactive Web UI

- [x] 4.1 Implement dependency injection in `src/presentation/api/dependencies.py` using `Annotated[..., Depends(...)]` type aliases adhering to FastAPI skill best practices, verified with unit tests.
- [x] 4.2 Implement API routers (`src/presentation/api/routers/documents.py`, `src/presentation/api/routers/query.py`, `src/presentation/api/routers/health.py`) with router-level prefix, tags, and explicit return types, verified with router tests.
- [x] 4.3 Create the FastAPI application in `src/presentation/api/main.py` with lifespan management and interactive web chat interface served at `GET /`, verified with TestClient.

## 5. Integration Verification and Quality Checks

- [x] 5.1 Create end-to-end integration tests validating language batch ingestion (`pt-br`, `en`) and semantic querying via async ASGI client, verified with `uv run pytest`.
- [x] 5.2 Verify complete codebase compliance by running `uv run ruff check .` and `uv run ruff format --check .`.
