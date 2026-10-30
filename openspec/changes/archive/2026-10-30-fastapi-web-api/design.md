# Design: FastAPI Async Web API and Batch Ingestion

## Context

See `proposal.md` for motivation. The system currently provides synchronous use cases and adapters tailored for the Typer CLI.

This change introduces an asynchronous presentation layer in `src/api/` powered by FastAPI, incorporating the conventions and best practices defined in `.agents/skills/fastapi/SKILL.md`. It also introduces automated batch ingestion by language folder (`docs/<language>/`) and an interactive browser-accessible interface.

## Goals / Non-Goals

**Goals:**

- Implement FastAPI application in `src/api/` with router segregation (`src/api/routers/`).
- Use `Annotated` style for all endpoint parameters and dependencies (`Annotated[..., Depends(...)]`, `Annotated[..., Query(...)]`).
- Declare explicit type aliases for dependencies (`IngestUseCaseDep`, `AskUseCaseDep`, etc.).
- Introduce asynchronous protocols and adapters (`AsyncOllamaAdapter` using `httpx.AsyncClient`, `AsyncInMemoryVectorAdapter`).
- Implement `AsyncBatchIngestByLanguageUseCase` scanning `docs/<language>/*.md` and ingesting all documents concurrently.
- Serve an interactive web chat and ingestion interface at `GET /` for browser-based interaction.
- Update `openapi.yaml` and re-generate `src/domain/models/schemas.py` via `datamodel-code-generator`.
- Configure `pyproject.toml` with `fastapi`, `uvicorn[standard]`, and `[tool.fastapi]` entrypoint.
- Write async unit and integration tests using `httpx.AsyncClient` and `fastapi.testclient.TestClient`.

**Non-Goals:**

- External JavaScript framework build toolchains (Node/Vite/Webpack); the web interface is self-contained.
- Deprecating or removing the existing Typer CLI (`src/cli/` remains fully operational).

## Decisions

### 1. Asynchronous Clean Architecture

- **Choice**: Implement async use cases (`AsyncIngestDocumentsUseCase`, `AsyncAskQuestionUseCase`, `AsyncBatchIngestByLanguageUseCase`) and async adapters (`AsyncOllamaAdapter` using `httpx.AsyncClient`).
- **Rationale**: FastAPI endpoints should not block the event loop during I/O operations (HTTP calls to Ollama and vector searches).
- **Alternatives considered**: Running synchronous use cases inside `fastapi.concurrency.run_in_threadpool`. Rejected because native async HTTP with HTTPX provides superior concurrency and resource efficiency.

### 2. Dependency Injection Pattern

- **Choice**: Define reusable dependencies in `src/api/dependencies.py` using `Annotated[..., Depends(...)]` with explicit type aliases.
- **Rationale**: Adheres strictly to the FastAPI guidelines in `fastapi/SKILL.md` and isolates adapter lifecycles.
- **Alternatives considered**: Instantiating adapters globally in route handlers. Rejected because it violates Dependency Inversion and makes testing with fakes difficult.

### 3. Language Batch Ingestion Mechanism

- **Choice**: Ingest all `.md` files found under `docs/<language>` (e.g. `docs/pt-br` or `docs/en`), attaching the filename as `source` and language as metadata.
- **Rationale**: Fulfills the user requirement to ingest knowledge bases by language without passing files individually.

### 4. Interactive Browser Experience

- **Choice**: Provide an interactive web interface served at `GET /` that allows users to select a language to ingest and ask questions in an interactive chat UI.
- **Rationale**: Delivers immediate web interactivity without requiring separate frontend build infrastructure.

## Architecture

```
Presentation:
  ├── src/cli/ (Typer CLI - Composition Root 1)
  └── src/api/ (FastAPI Web API - Composition Root 2)
       ├── main.py (FastAPI app, lifespan, frontend routing)
       ├── dependencies.py (Annotated dependency injection)
       └── routers/
            ├── documents.py (POST /documents/ingest, POST /documents/ingest/by-language)
            ├── query.py (POST /query)
            └── health.py (GET /health)

Application:
  └── src/application/use_cases/
       ├── ingest_documents.py (Async & sync document ingestion)
       ├── ask_question.py (Async & sync question answering)
       └── batch_ingest_language.py (Language directory scanner & batch ingestion)

Domain:
  ├── src/domain/interfaces/ (Async/Sync Protocols)
  ├── src/domain/entities/
  └── src/domain/models/ (Pydantic v2 schemas from openapi.yaml)

Infrastructure:
  └── src/infra/adapters/
       ├── ollama.py (Async & sync HTTPX Ollama client)
       └── in_memory_repository.py (Async & sync in-memory vector storage)
```

## Risks / Trade-offs

- **[In-Memory Concurrency]**: An in-memory vector list shared across async requests must avoid race conditions during batch insertion.
  - *Mitigation*: Vector operations append chunks in atomic Python list operations or use an asyncio lock during batch writes.
- **[Directory Path Resolution]**: Running the API from different working directories could affect `docs/` path resolution.
  - *Mitigation*: Resolve `docs/` relative to project root or configurable via `Settings`.
