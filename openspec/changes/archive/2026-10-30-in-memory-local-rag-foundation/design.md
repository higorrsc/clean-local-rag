# Design: In-Memory Local RAG Foundation

## Context

See `proposal.md` for motivation. The project is governed by `AGENTS.md`, enforcing Clean Architecture, SOLID, and Spec-Driven Design (SDD). External frameworks like LangChain are disallowed; prompt construction and orchestration are handled explicitly.

The current codebase contains skeletal directories and an empty `compose.yaml`. This design details how the foundational layers, SDD workflow, and in-memory RAG pipeline are constructed.

## Goals / Non-Goals

**Goals:**

- Establish the OpenAPI 3.1 specification (`openapi.yaml`) as the single source of truth for RAG schemas.
- Automate generation of Pydantic models into `src/domain/models.py` via `datamodel-code-generator`.
- Define Domain Protocols (`VectorRepository`, `EmbeddingGateway`, `LLMGateway`) and entity `DocumentChunk`.
- Implement `InMemoryVectorAdapter` computing cosine similarity via NumPy to allow fast, database-free execution.
- Implement `OllamaAdapter` using `httpx` for both embedding calculation (`nomic-embed-text`) and chat generation (`qwen3:4b-instruct`).
- Implement `IngestDocumentsUseCase` (chunking, embedding, storage) and `AskQuestionUseCase` (retrieval, prompt assembly, answer generation).
- Configure `compose.yaml` with PostgreSQL + `pgvector` and an Ollama service with an init container for automatic model pulling.
- Build a Typer CLI presentation layer wiring dependencies at the composition root.
- Validate the pipeline with automated tests using mocks/fakes.

**Non-Goals:**

- Production persistence via `pgvector` in this initial change (PostgreSQL container will be provisioned in `compose.yaml`, but the active application wiring uses `InMemoryVectorAdapter` for immediate zero-db testing).
- Complex semantic or agentic chunking algorithms (simple sliding-window chunker is used).
- Exposing REST API endpoints (reserved for a subsequent change; contracts are ready in OpenAPI).

## Decisions

### 1. Spec-Driven Design Workflow

- **Choice**: Write `openapi.yaml` with reusable component schemas (`IngestRequest`, `IngestResponse`, `QueryRequest`, `QueryResponse`, `ChunkMetadata`), and use `datamodel-code-generator` targeting Pydantic v2.
- **Rationale**: Guarantees architectural decoupling and ensures the CLI and future REST endpoints share identical DTO definitions without manual duplication.
- **Alternatives considered**: Manually writing Pydantic models in `src/domain/models.py`. Rejected due to violation of SDD principles established in `AGENTS.md`.

### 2. In-Memory Vector Search with NumPy

- **Choice**: Store chunks in an in-memory repository structure and evaluate top-k retrieval using cosine distance computed via `numpy.dot` normalized by vector norms.
- **Rationale**: Satisfies the requirement to run initial local tests without database dependency while strictly adhering to the `VectorRepository` Protocol.
- **Alternatives considered**: SQLite with sqlite-vss or FAISS. Rejected to avoid unnecessary native dependencies before pgvector integration.

### 3. Direct HTTPX Client for Ollama

- **Choice**: Use `httpx.Client` (or `AsyncClient`) communicating with `http://localhost:11434/api/embed` (or `/api/embeddings`) and `/api/chat`.
- **Rationale**: Lightweight, standard, and maintains complete control over payload formatting and temperature parameters without LangChain dependencies.
- **Alternatives considered**: `requests` (no async support, older API) or `ollama-python` library (adds unnecessary external wrapper when direct REST calls are straightforward and mandated by `AGENTS.md`).

### 4. Containerized Ollama with Model Pre-Puller

- **Choice**: In `compose.yaml`, define `postgres` (with `pgvector/pgvector:pg16`), `ollama`, and an auxiliary init service that executes `ollama pull nomic-embed-text` and `ollama pull qwen3:4b-instruct` into a shared Docker volume.
- **Rationale**: Provides a turn-key environment for users without Ollama installed on the host, while allowing host users to configure `OLLAMA_BASE_URL` in `.env`.
- **Alternatives considered**: Baking models directly into a Dockerfile image build. Rejected due to enormous image sizes and slow builds.

## Architecture & Layer Interaction

```text
 presentation/
   └── cli/main.py (Composition Root: injects adapters into use cases)
            │
            ▼
 application/
   └── use_cases.py
        ├── IngestDocumentsUseCase (chunks text, calls embedder, saves to repo)
        └── AskQuestionUseCase (embeds query, queries repo, builds prompt, calls LLM)
            │
            ▼
 domain/
   ├── interfaces.py (Protocols: VectorRepository, EmbeddingGateway, LLMGateway)
   ├── models.py     (Pydantic schemas generated from openapi.yaml)
   └── entities.py   (Domain entities: DocumentChunk)
            ▲
            │ (implements)
 infra/
   └── adapters/
        ├── in_memory_repository.py (InMemoryVectorAdapter via NumPy)
        └── ollama.py               (OllamaAdapter via HTTPX)
```

## Risks / Trade-offs

- **[State Ephemerality]**: An in-memory vector repository resets when the CLI process exits.
  - *Mitigation*: The CLI will support an interactive session/repl mode or single-run multi-step demonstration so users can ingest and query within the same session prior to persistent database integration.
- **[Docker Model Download Latency]**: Pulling models on first run can take several minutes depending on internet speed.
  - *Mitigation*: The init container logs progress, and users with host Ollama can skip Docker Ollama via `.env`.
