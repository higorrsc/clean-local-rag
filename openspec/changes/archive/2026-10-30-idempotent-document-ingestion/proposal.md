# Proposal: Idempotent Document Ingestion

## Why

Repeated document ingestion (such as multiple clicks on "Carregar Documentos" in the web UI or re-running CLI ingest on updated markdown files) creates duplicate chunks in the vector repository. Currently, every chunk receives a random `uuid.uuid4()`, bypassing conflict resolution and causing redundant chunks and diluted retrieval scores.

## What Changes

- Add source-based deletion (`delete_by_source` / `adelete_by_source`) to `VectorRepository` and `AsyncVectorRepository` interfaces and adapters.
- Ensure `IngestDocumentsUseCase` replaces existing chunks with the same `source` instead of duplicating them.
- Ensure `AsyncBatchIngestByLanguageUseCase` removes existing chunks belonging to the targeted language before persisting new chunks.
- Generate deterministic `chunk_id` identifiers derived from source and content to guarantee idempotency.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities

- `document-ingestion`: Update requirements to enforce idempotent ingestion where repeated ingestion replaces existing chunks rather than duplicating them.

## Impact

- `src/domain/interfaces/vector_repository.py`: Add `delete_by_source` and `adelete_by_source` protocol methods.
- `src/infra/adapters/in_memory_repository.py`: Implement synchronous and asynchronous `delete_by_source`.
- `src/infra/adapters/pgvector_repository.py`: Implement synchronous and asynchronous `delete_by_source` using raw SQL `DELETE FROM document_chunks WHERE source = %(source)s`.
- `src/application/use_cases/ingest_documents.py`: Clean previous chunks for the given `source` before persisting.
- `src/application/use_cases/batch_ingest_language.py`: Clean previous chunks for files or language before persisting.
- Unit and integration tests for idempotent behavior.
