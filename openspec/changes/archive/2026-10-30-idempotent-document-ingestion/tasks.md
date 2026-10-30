# Tasks

## 1. Domain Interfaces and Entity Enhancements

- [x] 1.1 Add `delete_by_source` and `delete_by_metadata` to `VectorRepository` and async variants to `AsyncVectorRepository` in `src/domain/interfaces/vector_repository.py`, verified with protocol check tests.
- [x] 1.2 Implement deterministic chunk ID generation helper based on source, index, and content hash, verified with entity/helper unit tests.

## 2. Repository Adapters Implementation

- [x] 2.1 Implement `delete_by_source` and `delete_by_metadata` (sync and async) in `InMemoryVectorAdapter` in `src/infra/adapters/in_memory_repository.py`, verified with unit tests.
- [x] 2.2 Implement `delete_by_source` and `delete_by_metadata` (sync and async) with raw SQL in `PgVectorAdapter` in `src/infra/adapters/pgvector_repository.py`, verified with mock and live repository tests.

## 3. Application Use Cases Idempotency

- [x] 3.1 Update `IngestDocumentsUseCase` to remove existing chunks for the same source before persisting and assign deterministic chunk IDs, verified with unit tests.
- [x] 3.2 Update `AsyncBatchIngestByLanguageUseCase` to remove existing chunks for the language before persisting and assign deterministic chunk IDs, verified with batch use case unit tests.

## 4. End-to-End Verification and Quality Checks

- [x] 4.1 Verify idempotent ingestion behavior via integration tests preventing duplicates on repeated runs for both backends, verified with `uv run pytest`.
- [x] 4.2 Verify codebase compliance by running `uv run ruff format --check .`, `uv run ruff check .`, and `uv run pytest`.
