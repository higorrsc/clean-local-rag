# Spec Delta: document-ingestion

## ADDED Requirements

### Requirement: Language Directory Batch Ingestion

The system SHALL accept a language code parameter, automatically scan the corresponding directory `docs/<language>`, and ingest all markdown files within it into the vector repository.

#### Scenario: Successful language directory ingestion

- **WHEN** user requests ingestion for language code `pt-br` or `en` with valid documents present
- **THEN** the system parses all markdown files in `docs/<language>`, chunks them, generates vector embeddings, and stores them in the vector repository

#### Scenario: Non-existent language directory

- **WHEN** user requests batch ingestion for an unsupported or non-existent language code
- **THEN** the system rejects the request and returns an error indicating that the directory does not exist
