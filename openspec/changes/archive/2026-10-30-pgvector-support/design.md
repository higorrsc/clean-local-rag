# Design: pgvector Storage Integration

## Context

The system currently relies exclusively on `InMemoryVectorAdapter` for storing and retrieving vector embeddings. While fast and isolated for testing, it lacks durability across application restarts. The repository already includes `pgvector/pgvector:pg16` in `compose.yaml` and lists `psycopg[binary]` and `pgvector` in dependencies.

In accordance with `AGENTS.md`, no ORM (like SQLAlchemy) will be introduced. All database interactions will use raw SQL with `psycopg` (v3) and native `pgvector` operations.

## Goals / Non-Goals

**Goals:**

- Implement `PgVectorAdapter` implementing `VectorRepository` and `AsyncVectorRepository` protocols using raw SQL.
- Provide idempotent DDL initialization ensuring the `vector` extension and `document_chunks` table exist.
- Use native pgvector cosine distance (`<=>`) to compute top-k similarity directly within Postgres.
- Allow dynamic selection of the repository backend (`memory` or `pgvector`) via `settings.vector_backend`.
- Maintain complete backwards compatibility by defaulting `vector_backend` to `"memory"`, preserving fast millisecond test execution without container requirements.

**Non-Goals:**

- Introducing ORM abstractions or migration frameworks (Alembic).
- External vector databases (Chroma, Qdrant, Milvus).
- Dynamic vector dimension auto-alteration (default configured for 768 dimensions corresponding to `nomic-embed-text`).

## Decisions

### 1. Direct Psycopg 3 Connection and Vector Registration

- **Decision:** Use `psycopg.connect` (sync) and `psycopg.AsyncConnection.connect` (async) with `pgvector.psycopg.register_vector` and `register_vector_async`.
- **Alternatives Considered:** SQLAlchemy or asyncpg.
- **Rationale:** `AGENTS.md` explicitly mandates raw SQL with `psycopg` to preserve Clean Architecture, avoid heavyweight framework bindings, and keep queries transparent.

### 2. Schema Design and Cosine Similarity Query

- **Schema:**

  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;

  CREATE TABLE IF NOT EXISTS document_chunks (
      chunk_id TEXT PRIMARY KEY,
      document_id TEXT,
      content TEXT NOT NULL,
      source TEXT,
      metadata JSONB DEFAULT '{}'::jsonb,
      embedding vector(768) NOT NULL
  );

  CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
  ON document_chunks USING hnsw (embedding vector_cosine_ops);
  ```

- **Similarity Calculation:**
  In pgvector, `<=>` returns cosine distance $d \in [0, 2]$. Cosine similarity is computed as $1 - d$:

  ```sql
  SELECT chunk_id, document_id, content, source, metadata,
         1 - (embedding <=> %(embedding)s::vector) AS similarity
  FROM document_chunks
  ORDER BY embedding <=> %(embedding)s::vector
  LIMIT %(top_k)s;
  ```

### 3. Factory and Presentation Injection

- In `src/infra/adapters/vector_factory.py`, provide `get_vector_repository(backend: str | None = None)`.
- When `vector_backend == "pgvector"`, instantiate `PgVectorAdapter(conn_str=settings.pg_dsn)`.
- When `vector_backend == "memory"`, instantiate `InMemoryVectorAdapter()`.
- Presentation roots (`src/presentation/cli/main.py` and `src/presentation/api/dependencies.py`) consume the factory.

## Risks / Trade-offs

- **[PostgreSQL connection unavailability when configured for pgvector]** → Adapter verifies connection during initialization and raises clear, actionable `ConnectionError` with instructions to run `docker compose up -d postgres`.
- **[Test performance with database dependencies]** → Unit tests use mock psycopg connections or in-memory repository; integration tests against live pgvector are opt-in or conditionally run when Postgres is healthy.
