# Spec Delta: document-ingestion

## ADDED Requirements

### Requirement: Configurable Vector Storage Backend

The system SHALL support configuring the active vector repository backend (in-memory or PostgreSQL with pgvector) via environment settings without modifying domain contracts or application use cases.

#### Scenario: In-memory backend configuration

- **WHEN** application starts with `vector_backend` set to `memory`
- **THEN** vector operations use the in-memory repository adapter

#### Scenario: PgVector backend configuration

- **WHEN** application starts with `vector_backend` set to `pgvector`
- **THEN** vector operations connect to PostgreSQL and persist/retrieve chunks using native pgvector cosine distance operations

#### Scenario: Database table initialization

- **WHEN** `pgvector` backend is initialized
- **THEN** the system ensures the `vector` extension and `document_chunks` table exist before executing queries
