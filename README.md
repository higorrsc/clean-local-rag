# 🧠 Local RAG CLI & Web API

A modular, **100% Local, Private, and Secure RAG (Retrieval-Augmented Generation)** application built with Python according to **Clean Architecture**, **Domain-Driven Design (DDD)**, **SOLID**, and **Spec-Driven Design (SDD)** principles.

---

## 📌 Overview

This project provides an end-to-end local semantic search and context-grounded answer generation solution using local LLM models via **Ollama** and vector similarity with **Cosine Similarity** in memory, with support for **pgvector**.

### ✨ Key Features

- **100% Local & Secure:** No reliance on external LLM APIs (such as OpenAI or Anthropic); your data never leaves your local environment.
- **No Opaque Frameworks:** Free from LangChain or LlamaIndex abstractions. Orchestration, prompt construction, and chunking strategies are implemented manually with full control and transparency.
- **Spec-Driven Design (SDD):** Contracts strictly defined in [openapi.yaml](openapi.yaml) as the single source of truth, with Pydantic models automatically generated via `datamodel-code-generator`.
- **Dual Presentation Layer (CLI & Web API):**
  - **Interactive & Single-Command CLI:** Built with **Typer** and **Rich**.
  - **Asynchronous REST API & Web UI:** Built with **FastAPI**, featuring automatic Swagger documentation and an interactive browser chat interface with zero external CDN dependencies.
- **Language-Based Batch Ingestion:** Ability to automatically scan and ingest all markdown files grouped in language directories (`docs/<language>/*.md`).
- **Bilingual Knowledge Base Included:** Practical barbershop chain examples provided in Portuguese (`docs/pt-br/`) and English (`docs/en/`).

---

## 🏛️ Architecture & Design Principles

The application strictly enforces concentric boundaries defined by **Clean Architecture**:

```text
Presentation (CLI / Typer, REST API & Web UI / FastAPI)
     ↓
Application (Use Cases: Ingestion, Semantic Query, Batch by Language)
     ↓
Domain (Entities, Protocols, OpenAPI-generated Models)
     ↑
Infrastructure (Ollama via HTTPX, In-Memory Vector Repository / PgVector via Psycopg)
```

### 📂 Directory Structure

```text
rag_project/
├── openapi.yaml                 # OpenAPI specification (Single Source of Truth)
├── pyproject.toml               # Dependencies and tools managed with uv
├── compose.yaml                 # Docker infrastructure (Ollama + PgVector)
├── .env.example                 # Environment variables template
├── docs/                        # Sample bilingual knowledge base
│   ├── pt-br/                   # Portuguese documents
│   └── en/                      # English documents
├── src/
│   ├── config/                  # Centralized settings via pydantic-settings
│   ├── domain/                  # Domain core (Entities, Interfaces, and SDD Models)
│   │   ├── entities/            # DocumentChunk entity
│   │   ├── interfaces/          # Protocols (Embedding, LLM, and Vector Repositories)
│   │   └── models/              # Pydantic models generated from openapi.yaml
│   ├── application/             # RAG orchestration use cases
│   │   └── use_cases/           # Single ingest, semantic ask, and language batch ingest
│   ├── infra/                   # Infrastructure adapters
│   │   └── adapters/            # OllamaAdapter (HTTPX sync/async), InMemoryVectorAdapter
│   └── presentation/            # Presentation layer
│       ├── cli/                 # Typer CLI application (interactive & command modes)
│       └── api/                 # FastAPI Web API and chat UI
└── tests/                       # Segregated test suite mirroring src/
    ├── domain/                  # Entity and protocol check tests
    ├── infra/                   # Adapter tests with mocked HTTP transports
    ├── application/             # Unit tests for use cases
    └── presentation/            # End-to-end tests for CLI and FastAPI ASGI app
```

---

## 📋 Prerequisites

- **Python:** `>= 3.15`
- **Package Manager:** [uv](https://github.com/astral-sh/uv) (fast, deterministic)
- **Ollama:** Installed locally or run via Docker with the following models:
  - `nomic-embed-text` (768-dimensional embedding generation)
  - `qwen3:4b-instruct` (instruction-tuned LLM for context-grounded reasoning)
- **Docker & Docker Compose** (optional, to run the complete containerized stack)

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd rag-cli
```

### 2. Configure Environment Variables

Copy the environment variables template:

```bash
cp .env.example .env
```

Edit `.env` if necessary. Defaults are preconfigured for local use:

```dotenv
PG_DSN=postgresql://dev:dev@localhost:5432/rag_db
OLLAMA_BASE_URL=http://localhost:11434/api
EMBED_MODEL=nomic-embed-text:latest
CHAT_MODEL=qwen3:4b-instruct
```

### 3. Install Dependencies

Using `uv`:

```bash
uv sync
```

### 4. Pull Models in Ollama

If you have Ollama running locally on your host:

```bash
ollama pull nomic-embed-text
ollama pull qwen3:4b-instruct
```

Alternatively, start the complete stack with Docker Compose (which pulls models automatically on startup):

```bash
docker compose up -d
```

---

## 💻 Usage

### 1. CLI (Command-Line Interface)

The CLI provides both an interactive in-memory session mode and direct single commands.

#### 💬 Interactive Session Mode (Recommended for Terminal Testing)

Maintains indexed chunks across sequential prompts:

```bash
uv run python -m src.presentation.cli interactive
```

Inside the interactive session:

```text
rag-cli> ingest docs/en/overview-and-branches.md
✓ Ingestão concluída: 7 chunks de overview-and-branches.md (Total: 7)

rag-cli> ingest docs/en/services-and-pricing.md
✓ Ingestão concluída: 6 chunks de services-and-pricing.md (Total: 13)

rag-cli> ask Which branch is exclusively dedicated to women and what services does it offer?
Resposta:
The branch exclusively dedicated to women is the Studio Femme branch, offering specialized salon services...

rag-cli> status
Chunks indexados: 13

rag-cli> exit
```

#### ⚡ Direct Single Commands

- **Ingest text directly:**

  ```bash
  uv run python -m src.presentation.cli ingest --text "Imperial Barbershop was founded in 2018." --source "history.txt"
  ```

- **Ingest a document file:**

  ```bash
  uv run python -m src.presentation.cli ingest --file docs/en/overview-and-branches.md
  ```

- **Ask a question:**

  ```bash
  uv run python -m src.presentation.cli ask "What are the available branches?"
  ```

- **Display help:**

  ```bash
  uv run python -m src.presentation.cli --help
  ```

---

### 2. Web API (FastAPI) & Interactive Web UI

The asynchronous API allows integration into downstream services or direct interaction via browser.

#### 🌐 Start the Development Server

```bash
uv run fastapi dev
```

> The application will listen on `http://127.0.0.1:8000`.

- **Interactive Web Chat UI:** Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.
  - Select your desired language (`pt-br` or `en`) and click **Carregar Documentos** to batch-ingest all files from `docs/<language>`.
  - Type questions in the chat box to receive responses with source references and similarity scores.
- **Interactive Swagger Documentation:** Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
- **ReDoc Documentation:** Open [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc).

#### 🚀 Start in Production Mode

```bash
uv run fastapi run
```

---

## 📡 REST API Endpoints

| Method | Endpoint | Description | Sample Payload |
| --- | --- | --- | --- |
| `GET` | `/health` | Service readiness and health status | *None* |
| `POST` | `/documents/ingest` | Ingest and vectorize a single text document | `{"content": "Text...", "source": "doc.md"}` |
| `POST` | `/documents/ingest/by-language` | Batch ingest all markdown documents for a language | `{"language": "en"}` |
| `POST` | `/query` | Semantic search and LLM context-grounded answer | `{"question": "What is the haircut price?", "top_k": 4}` |

---

## 🧪 Testing & Code Quality

Strict quality checks are enforced across the repository:

### Run the Test Suite

Tests cover domain protocols, adapters with mock transports, application use cases, and ASGI E2E integration:

```bash
uv run pytest
```

### Code Formatting

```bash
uv run ruff format .
```

### Static Analysis & Linting

```bash
uv run ruff check .
```

### Complete Pre-Commit Validation

```bash
uv run ruff format --check . && uv run ruff check . && uv run pytest
```

### Regenerate SDD Models (OpenAPI)

When modifying [openapi.yaml](openapi.yaml), regenerate Pydantic models with:

```bash
uv run datamodel-codegen --input openapi.yaml --output src/domain/models/schemas.py --input-file-type openapi --output-model-type pydantic_v2.BaseModel
```

---

## 📝 Commit Conventions

All commits adhere to **Conventional Commits** paired with **Gitmoji**:

- ✨ `feat:` New features (e.g., `feat(api): add batch language ingest endpoint`)
- 🐛 `fix:` Bug fixes
- 📝 `docs:` Documentation updates or contract changes
- ♻️ `refactor:` Code refactoring without behavior change
- ✅ `test:` Adding or updating tests
- 🔧 `chore:` Build scripts, dependencies, or tool configuration

---

## 📄 License

This project is created for portfolio and advanced architectural reference for Local RAG in Python. Feel free to use and adapt as needed.
