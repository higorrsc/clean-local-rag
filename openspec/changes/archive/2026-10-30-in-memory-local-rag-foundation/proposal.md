# Proposal: In-Memory Local RAG Foundation

## Why

This project is a greenfield Local RAG (Retrieval-Augmented Generation) application designed with Clean Architecture, Domain-Driven Design (DDD), SOLID, and Spec-Driven Design (SDD).
To enable fast iteration, local verification, and self-contained reproducibility without external cloud dependencies or immediate database setup, we need to establish the foundational architecture, local containerized infrastructure (Ollama + PostgreSQL pgvector), OpenAPI schema contracts, and an in-memory vector pipeline for end-to-end question answering.

## What Changes

- **Dependency Realignment**: Align `pyproject.toml` with `AGENTS.md` by introducing `httpx`, `psycopg[binary]`, `pgvector`, `typer`, `datamodel-code-generator`, and `pytest`, while removing `requests` and `pydantic-ai` to ensure manual prompt and orchestration control.
- **Local Infrastructure Setup**: Define `compose.yaml` declaring PostgreSQL with `pgvector` alongside an Ollama service and an initialization service to pull required models (`nomic-embed-text` and `qwen3:4b-instruct`) for complete out-of-the-box local execution.
- **Spec-Driven Design Contracts**: Define `openapi.yaml` as the single source of truth for RAG request/response schemas, and establish code generation with `datamodel-code-generator` producing `src/domain/models.py`.
- **Domain Protocols**: Define domain entities (`DocumentChunk`) and interfaces (`EmbeddingGateway`, `LLMGateway`, `VectorRepository`) in `src/domain/`.
- **In-Memory & Ollama Adapters**: Implement `InMemoryVectorAdapter` (using NumPy for cosine similarity `<=>`) and `OllamaAdapter` (via `httpx` for embeddings and generation).
- **Core Use Cases**: Implement `IngestDocumentsUseCase` and `AskQuestionUseCase` in `src/application/use_cases.py`.
- **Presentation CLI**: Build Typer commands in `src/cli/` allowing ingestion and querying from the terminal against the in-memory pipeline.
- **Automated Tests**: Provide unit and integration test coverage using fakes/mocks.

## Capabilities

### New Capabilities

- `document-ingestion`: Ingesting raw document content, chunking, calculating embeddings via local Ollama, and storing chunks in the vector repository.
- `knowledge-retrieval`: Processing user queries, calculating query embeddings, retrieving relevant chunks by cosine similarity, augmenting the context prompt, and generating answers with local LLM.

### Modified Capabilities
<!-- None: Greenfield project -->

## Impact

- **Dependencies**: Adds `httpx`, `psycopg[binary]`, `pgvector`, `typer`, `datamodel-code-generator`, `pytest`.
- **Architecture**: Enforces Clean Architecture boundaries with Domain, Application, Infrastructure, and Presentation layers.
- **Local Environment**: Provides docker compose definitions for Postgres/pgvector and Ollama model pre-fetching.
