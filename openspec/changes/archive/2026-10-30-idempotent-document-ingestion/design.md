# Design: Idempotent Document Ingestion

## Context

Document ingestion currently generates non-deterministic random chunk IDs (`uuid.uuid4()`) and performs append-only inserts. When an existing document or an entire language directory (`docs/<language>`) is re-ingested, the repository accumulates duplicate chunks, inflating chunk counts and degrading retrieval quality.

## Goals / Non-Goals

**Goals:**

- Extend `VectorRepository` and `AsyncVectorRepository` with deletion capabilities by source identifier and metadata key/value.
- Implement source/language cleanup before storing new chunks in both `IngestDocumentsUseCase` and `AsyncBatchIngestByLanguageUseCase`.
- Use deterministic chunk ID generation based on document source, index, and content hash.
- Ensure identical results and chunk counts across arbitrary repeated ingestions in both `memory` and `pgvector` backends.

**Non-Goals:**

- Soft-deletion or historical chunk versioning.
- File-system watch daemons or automatic change listeners.

## Decisions

### 1. Repository Interface Extension (`delete_by_source` & `delete_by_metadata`)

- **Decision:** Add `delete_by_source(source: str) -> None` and `delete_by_metadata(key: str, value: Any) -> None` (along with async variants `adelete_by_source` and `adelete_by_metadata`) to the domain protocols.
- **Alternatives Considered:** Complete repository wipe (`clear()`) before any ingestion.
- **Rationale:** A complete wipe would destroy chunks from unrelated documents or other languages. Scoped deletion removes only the superseded chunks.

### 2. Implementation in Repository Adapters

- **InMemoryVectorAdapter:**
  Filters `self._chunks` in place:

  ```python
  self._chunks = [c for c in self._chunks if c.source != source]
  ```

- **PgVectorAdapter:**
  Executes raw SQL parameter binding:

  ```sql
  DELETE FROM document_chunks WHERE source = %(source)s;
  DELETE FROM document_chunks WHERE metadata->>%(key)s = %(value)s;
  ```

### 3. Deterministic Chunk Identification

- **Decision:** Derive `chunk_id` using `uuid.uuid5(uuid.NAMESPACE_DNS, f"{source}:{idx}:{content_hash}")`.
- **Alternatives Considered:** Random `uuid.uuid4()`.
- **Rationale:** Guarantees idempotency even if chunks are saved in concurrently running jobs with `ON CONFLICT (chunk_id) DO UPDATE`.

## Risks / Trade-offs

- **[Interrupted ingestion leaving source partially empty]** → In PostgreSQL, the deletion and insertions can be wrapped in a transaction block so partial ingestion does not result in lost data.
