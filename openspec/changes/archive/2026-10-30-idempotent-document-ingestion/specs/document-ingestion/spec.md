# Spec Delta: document-ingestion

## MODIFIED Requirements

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
