# Tasks

## 1. Dependencies and Infrastructure Setup

- [x] 1.1 Update `pyproject.toml` with runtime dependencies (`httpx`, `psycopg[binary]`, `pgvector`, `typer`, `numpy`, `pydantic-settings`) and development dependencies (`datamodel-code-generator`, `pytest`, `ruff`), removing `requests` and `pydantic-ai`, and verify with `uv sync`.
- [x] 1.2 Define `compose.yaml` declaring PostgreSQL with `pgvector/pgvector:pg16`, Ollama service, and an init container pulling `nomic-embed-text` and `qwen3:4b-instruct`, verifying syntax with `docker compose config`.

## 2. Spec-Driven Design Contracts and Domain Layer

- [x] 2.1 Create `openapi.yaml` specifying contracts and schemas for document ingestion (`IngestRequest`, `IngestResponse`) and semantic retrieval (`QueryRequest`, `QueryResponse`), verifying schema validity.
- [x] 2.2 Generate Pydantic models in `src/domain/models.py` using `datamodel-code-generator` from `openapi.yaml`, verifying by importing generated models in Python.
- [x] 2.3 Implement domain entity `DocumentChunk` in `src/domain/entities.py` and protocols `VectorRepository`, `EmbeddingGateway`, and `LLMGateway` in `src/domain/interfaces.py`, verifying protocol definitions with unit tests.

## 3. Infrastructure Adapters

- [x] 3.1 Implement `InMemoryVectorAdapter` in `src/infra/adapters/in_memory_repository.py` using NumPy for cosine similarity, and verify with unit tests for storing and retrieving top-k chunks.
- [x] 3.2 Implement `OllamaAdapter` in `src/infra/adapters/ollama.py` using `httpx` for embedding generation and chat completions, and verify with unit tests using mocked HTTP responses.

## 4. Application Use Cases

- [x] 4.1 Implement `IngestDocumentsUseCase` in `src/application/use_cases.py` handling chunking, embedding generation, and repository persistence, verified with unit tests using mock gateways.
- [x] 4.2 Implement `AskQuestionUseCase` in `src/application/use_cases.py` handling query embedding, top-k retrieval, prompt augmentation, and LLM invocation, verified with unit tests using mock gateways.

## 5. Presentation Layer and Verification

- [x] 5.1 Implement Typer CLI commands in `src/cli/` wiring adapters and use cases at the composition root, verifying CLI execution with `uv run python -m src.cli --help`.
- [x] 5.2 Create end-to-end integration test validating ingestion and question answering through the in-memory pipeline, verified with `uv run pytest`.
- [x] 5.3 Verify codebase compliance by running `uv run ruff check` and `uv run ruff format --check`.
