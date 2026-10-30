# Spec Delta: web-api

## Purpose

Provides an asynchronous HTTP REST API and interactive browser-accessible interface to manage document ingestion, health monitoring, and semantic question answering.

## ADDED Requirements

### Requirement: Asynchronous REST Endpoints

The system SHALL expose asynchronous HTTP REST endpoints for single-document ingestion, language-based batch ingestion, and semantic query execution.

#### Scenario: Async document ingestion

- **WHEN** client sends a POST request with document content
- **THEN** the system asynchronously processes and indexes the document, returning 200 OK with chunk count and document ID

#### Scenario: Async language batch ingestion

- **WHEN** client sends a POST request to ingest documents by language code
- **THEN** the system asynchronously ingests all documents from the language directory and returns the total chunks and files ingested

#### Scenario: Async semantic query

- **WHEN** client sends a POST request with a user question
- **THEN** the system asynchronously retrieves similar chunks, queries the local LLM, and returns the natural language response and sources

### Requirement: Service Health Status Endpoint

The system SHALL expose an asynchronous GET endpoint at `/health` to verify service readiness and operational status.

#### Scenario: Health check success

- **WHEN** client sends a GET request to `/health`
- **THEN** the system responds with HTTP status 200 and a JSON payload indicating active status

### Requirement: Interactive Web Interface

The system SHALL serve an interactive HTML web interface allowing users to ingest documents by language and submit queries interactively from a web browser.

#### Scenario: Interactive web interface access

- **WHEN** user accesses the root web URL `/` in a browser
- **THEN** the system returns an interactive HTML interface equipped with ingestion controls and a query chat console
