# document-ingestion Specification

## Purpose

Provides capabilities to receive raw text documents, partition content into manageable chunks, generate vector embeddings, and store them for similarity search.

## Requirements

### Requirement: Document Content Ingestion

The system SHALL accept raw document text and optional source metadata, partitioning the text into sequential chunks with configurable chunk size and overlap. When a document source is provided and already exists in the repository, the ingestion SHALL replace the previous chunks for that source idempotently.

#### Scenario: Ingestion of valid text document

- **WHEN** user submits document text with an optional source name
- **THEN** the system partitions the text into indexed document chunks and confirms chunk generation

#### Scenario: Ingestion of empty content

- **WHEN** user submits an empty or whitespace-only document content
- **THEN** the system rejects the request and returns a validation error without persisting chunks

#### Scenario: Re-ingestion replaces existing document chunks

- **WHEN** user re-submits document text with a source identifier that is already present in the vector repository
- **THEN** the system replaces the previous chunks associated with that source without generating duplicate records

### Requirement: Embedding Generation for Chunks

The system SHALL generate high-dimensional vector representations for each document chunk via the configured local embedding service.

#### Scenario: Successful embedding vector calculation

- **WHEN** valid document chunks are processed
- **THEN** each chunk is assigned an embedding vector matching the expected dimensions of the embedding model

### Requirement: Vector Storage Persistence

The system SHALL store document chunks along with their vector embeddings and metadata in the active vector repository.

#### Scenario: Chunks stored in vector repository

- **WHEN** chunks with embeddings are saved
- **THEN** the vector repository confirms persistence and makes the chunks available for similarity search

### Requirement: Language Directory Batch Ingestion

The system SHALL accept a language code parameter, automatically scan the corresponding directory `docs/<language>`, and ingest all markdown files within it into the vector repository. Re-ingesting a language directory SHALL replace previously ingested chunks for that language.

#### Scenario: Successful language directory ingestion

- **WHEN** user requests ingestion for language code `pt-br` or `en` with valid documents present
- **THEN** the system parses all markdown files in `docs/<language>`, chunks them, generates vector embeddings, and stores them in the vector repository

#### Scenario: Non-existent language directory

- **WHEN** user requests batch ingestion for an unsupported or non-existent language code
- **THEN** the system rejects the request and returns an error indicating that the directory does not exist

#### Scenario: Batch re-ingestion replaces existing language chunks

- **WHEN** user requests batch ingestion for a language whose documents were previously ingested
- **THEN** the system removes previous chunks belonging to that language before persisting the newly scanned chunks, keeping chunk count consistent

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

