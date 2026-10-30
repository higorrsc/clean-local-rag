# Tasks

## 1. Configuration and Repository Factory

- [x] 1.1 Add `vector_backend: Literal["memory", "pgvector"] = "memory"` to `Settings` in `src/config/settings.py`, verified with configuration unit tests.
- [x] 1.2 Implement `create_vector_repository(backend: str | None = None)` in `src/infra/adapters/vector_factory.py`, verified with unit tests.

## 2. PgVector Repository Adapter Implementation

- [x] 2.1 Implement idempotent DDL schema initialization in `src/infra/adapters/pgvector_repository.py` creating the `vector` extension and `document_chunks` table with HNSW index, verified with mock connection tests.
- [x] 2.2 Implement synchronous methods (`save_chunks`, `search_similar`, `count`, `clear`) in `PgVectorAdapter` fulfilling the `VectorRepository` protocol, verified with unit tests.
- [x] 2.3 Implement asynchronous methods (`asave_chunks`, `asearch_similar`) in `PgVectorAdapter` fulfilling the `AsyncVectorRepository` protocol, verified with async unit tests.

## 3. Presentation Layer Integration

- [x] 3.1 Update CLI composition root in `src/presentation/cli/main.py` to obtain the vector repository via `create_vector_repository()`, verified with CLI command tests.
- [x] 3.2 Update FastAPI dependency injection in `src/presentation/api/dependencies.py` to obtain the vector repository via `create_vector_repository()`, verified with existing API endpoint tests.

## 4. End-to-End Verification and Quality Checks

- [x] 4.1 Create integration tests verifying `PgVectorAdapter` vector insertion, cosine similarity calculations (`1 - <=>`), and error handling, verified with `uv run pytest`.
- [x] 4.2 Verify codebase compliance by running `uv run ruff format --check .`, `uv run ruff check .`, and `uv run pytest`.
