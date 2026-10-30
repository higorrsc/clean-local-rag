# Proposal: pgvector-support

## Why

Currently, vector persistence and similarity retrieval in the application are limited to `InMemoryVectorAdapter`. While sufficient for quick prototyping and isolated tests, the in-memory store loses all indexed chunks upon process termination and cannot scale to larger document collections.

Integrating `pgvector` via PostgreSQL enables durable vector persistence, native database-level cosine similarity indexing (`<=>`), and seamless switching between in-memory and production-grade database storage without modifying application use cases or domain entities.

## What Changes

- Implement `PgVectorAdapter` in `src/infra/adapters/pgvector_repository.py` implementing both `VectorRepository` and `AsyncVectorRepository` protocols using raw SQL via `psycopg` (v3) and native `pgvector` extension.
- Create an automated table initializer creating the `document_chunks` table with `id`, `document_id`, `content`, `source`, `metadata JSONB`, and `embedding vector(768)` with an HNSW or IVFFlat index.
- Add `vector_backend` configuration setting in `src/config/settings.py` with values `"memory"` or `"pgvector"`.
- Update presentation dependency composition roots in `src/presentation/cli/main.py` and `src/presentation/api/dependencies.py` to instantiate the appropriate repository adapter based on configuration.
- Implement comprehensive unit tests with mocked psycopg connections and integration tests.

## Capabilities

### Modified Capabilities

- `document-ingestion`: Add requirement for configurable vector storage persistence supporting durable database backends alongside in-memory storage.

## Impact

- **Infrastructure:** Adds `PgVectorAdapter` in `src/infra/adapters/pgvector_repository.py`.
- **Configuration:** Adds `vector_backend: Literal["memory", "pgvector"] = "memory"` to `src/config/settings.py`.
- **Presentation:** CLI and FastAPI will inject `PgVectorAdapter` when `VECTOR_BACKEND=pgvector` is configured.
- **Dependencies:** `psycopg[binary]>=3.2.0` and `pgvector>=0.3.0` are already specified in `pyproject.toml`.
- **Backwards Compatibility:** Defaults to `"memory"` to ensure existing automated tests and CLI runs without PostgreSQL continue to pass seamlessly.
