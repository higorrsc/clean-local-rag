# 🧠 Local RAG CLI & Web API

A modular, **100% Local, Private, and Secure RAG (Retrieval-Augmented Generation)** application built with Python according to **Clean Architecture**, **Domain-Driven Design (DDD)**, **SOLID**, and **Spec-Driven Design (SDD)** principles.

---

## 📌 Overview

This project provides an end-to-end local semantic search and context-grounded answer generation solution using local LLM models via **Ollama** and pluggable vector storage:

- **In-Memory Vector Repository**: Zero-dependency, ephemeral, and fast cosine similarity retrieval (ideal for quick tests and lightweight CLI sessions).
- **PostgreSQL with pgvector**: Production-grade persistent vector storage using native Cosine Distance (`<=>`) operations, powered by `psycopg` and `pgvector`.

### ✨ Key Features

- **100% Local & Secure:** No reliance on external LLM APIs (such as OpenAI or Anthropic); your data never leaves your local environment.
- **No Opaque Frameworks:** Free from LangChain or LlamaIndex abstractions. Orchestration, prompt construction, and chunking strategies are implemented manually with full control, testability, and transparency.
- **Spec-Driven Design (SDD):** Contracts strictly defined in [openapi.yaml](openapi.yaml) as the single source of truth, with Pydantic models automatically generated via `datamodel-code-generator`.
- **Pluggable Vector Backends (`memory` | `pgvector`):** Switch effortlessly between in-memory and persistent PostgreSQL vector storage via the `VECTOR_BACKEND` environment variable or the `--backend` (`-b`) CLI flag.
- **Idempotent Ingestion:** Re-ingesting a document by file or source identifier automatically updates and replaces prior chunks instead of creating duplicates, using deterministic UUIDv5 chunk identifiers.
- **Dual Presentation Layer (CLI & Web API):**
  - **Interactive & Single-Command CLI:** Built with **Typer** and **Rich**, with real-time active backend badges and session inspection commands (`status`).
  - **Asynchronous REST API & Web UI:** Built with **FastAPI**, featuring automatic Swagger documentation and an interactive browser chat interface with zero external CDN dependencies.
- **Language-Based Batch Ingestion:** Automatically scans and ingests all markdown files grouped in language directories (`docs/<language>/*.md`).
- **Bilingual Knowledge Base Included:** Practical barbershop chain examples provided in Portuguese (`docs/pt-br/`) and English (`docs/en/`).
- **Shared State Across Interfaces:** When using `pgvector`, documents ingested via the Web UI are instantly queryable in the CLI and vice-versa.

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
Infrastructure (Ollama via HTTPX, In-Memory Repository, PgVector via Psycopg)
```

### 📂 Directory Structure

```text
clean-local-rag/
├── openapi.yaml                 # OpenAPI specification (Single Source of Truth)
├── pyproject.toml               # Dependencies and tools managed with uv
├── compose.yaml                 # Docker infrastructure (Ollama + PgVector + Auto-pull)
├── Makefile                     # Project workflow automation (start, pull, test, run)
├── scripts/                     # Smart infrastructure orchestration & model scripts
│   ├── setup-infra.sh           # Smart infra starter (Host Ollama detection vs Docker Compose)
│   └── pull-models.sh           # Local Ollama model puller
├── .env.example                 # Environment variables template
├── docs/                        # Sample bilingual knowledge base and media assets
│   ├── assets/                  # Demo GIFs and screenshots
│   ├── pt-br/                   # Portuguese documents
│   └── en/                      # English documents
├── src/
│   ├── config/                  # Centralized settings via pydantic-settings
│   ├── domain/                  # Domain core (Entities, Interfaces, and SDD Models)
│   │   ├── entities/            # DocumentChunk entity & deterministic UUID generator
│   │   ├── interfaces/          # Protocols (Embedding, LLM, and Vector Repositories)
│   │   └── models/              # Pydantic models generated from openapi.yaml
│   ├── application/             # RAG orchestration use cases
│   │   └── use_cases/           # Ingest, semantic query, and language batch ingest
│   ├── infra/                   # Infrastructure adapters
│   │   └── adapters/            # OllamaAdapter, InMemoryVectorAdapter, PgVectorAdapter, Factory
│   └── presentation/            # Presentation layer
│       ├── cli/                 # Typer CLI application (interactive & single commands)
│       └── api/                 # FastAPI Web API and chat UI
└── tests/                       # Segregated test suite mirroring src/
    ├── domain/                  # Entity and protocol check tests
    ├── infra/                   # Adapter tests (mocked HTTP & live pgvector integration)
    ├── application/             # Unit tests for use cases with fakes
    └── presentation/            # End-to-end tests for CLI and FastAPI ASGI app
```

---

## 📋 Prerequisites

- **Python:** `>= 3.15`
- **Package Manager:** [uv](https://github.com/astral-sh/uv) (fast, deterministic)
- **Docker & Docker Compose:** Required to run PostgreSQL with `pgvector` and Ollama
- **Ollama Models:**
  - `nomic-embed-text` (768-dimensional embedding generation)
  - `qwen3:4b-instruct` (instruction-tuned LLM for context-grounded reasoning)

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/higorrsc/clean-local-rag.git
cd clean-local-rag
```

### 2. Configure Environment Variables

Copy the environment variables template:

```bash
cp .env.example .env
```

Configure `.env` according to your desired backend:

```dotenv
# Vector storage backend: 'memory' or 'pgvector'
VECTOR_BACKEND=pgvector

# PostgreSQL with pgvector connection string
PG_DSN=postgresql://dev:dev@localhost:5432/rag_db

# Ollama API settings
OLLAMA_BASE_URL=http://localhost:11434/api
EMBED_MODEL=nomic-embed-text:latest
CHAT_MODEL=qwen3:4b-instruct
```

### 3. Install Python Dependencies

Using `uv`:

```bash
uv sync
```

### 4. Start Infrastructure (Smart Orchestration via Makefile)

Use the `Makefile` to initialize the infrastructure intelligently:

```bash
make up
```

#### ⚙️ How the orchestration works (`scripts/setup-infra.sh`)

1. **Local Ollama detected on host:** If the `ollama` binary is installed on your system, the script **does not** start the containerized Ollama (avoiding port `11434` conflicts and CPU overhead). It starts **only PostgreSQL with `pgvector`** (`docker compose up -d postgres`) and validates whether the required models (`nomic-embed-text` and `qwen3:4b-instruct`) are already downloaded.
   - If any required model is missing, it alerts you and suggests running:

     ```bash
     make pull-models
     ```

2. **Local Ollama not detected:** If you do not have Ollama installed locally, the script starts the **full stack** via Docker Compose (`postgres` + `ollama` + `ollama-init`), where the helper service downloads the models automatically.

To shut down the infrastructure at any time:

```bash
make down
```

---

## 🛠️ Makefile Commands

The project includes a `Makefile` with shortcuts for common development and infrastructure workflows:

| Command | Description |
| :--- | :--- |
| `make up` | Starts infrastructure intelligently (Postgres only if local Ollama exists, or full Docker stack). |
| `make down` | Stops and removes all Docker Compose containers. |
| `make pull-models` | Pulls required models (`nomic-embed-text` and `qwen3:4b-instruct`) in local Ollama. |
| `make status` | Displays the status of Docker containers and local Ollama models. |
| `make ingest` | Ingests the sample document (`docs/pt-br/visao-geral-e-unidades.md`) into the active backend. |
| `make cli` | Launches the interactive terminal CLI session. |
| `make api` | Starts the FastAPI development server (Swagger at `/docs` and Web Chat UI at `/`). |
| `make test` | Runs the test suite via `pytest`. |
| `make lint` | Runs static code analysis via `ruff check`. |
| `make format` | Formats code via `ruff format`. |
| `make check` | Runs `lint` and `test` sequentially. |
| `make help` | Displays formatted list of available targets. |

---

## 💻 Usage

### 1. CLI (Command-Line Interface)

The CLI supports both an interactive terminal session and single-shot commands, with explicit backend indicator panels.

![CLI Interactive Demo](docs/assets/demo-cli.gif)

#### 💬 Interactive Session Mode

Launch an interactive session:

```bash
# Uses backend from .env (e.g. PGVECTOR)
uv run python -m src.presentation.cli interactive

# Or explicitly select the backend via flag
uv run python -m src.presentation.cli interactive --backend pgvector
uv run python -m src.presentation.cli interactive --backend memory
```

Inside the interactive prompt:

```text
╭─────────────────────────────── Bem-vindo ao RAG CLI ─────────────────────────────────╮
│ Modo Interativo RAG Local (Backend: PGVECTOR)                                        │
│                                                                                      │
│ Comandos disponíveis:                                                                │
│   ingest <arquivo> ou ingest -f <arquivo> - Ingestão de arquivo                      │
│   ingest <texto> ou ingest -t <texto>     - Ingestão de texto                        │
│   ask <pergunta>                          - Fazer uma pergunta sobre o contexto      │
│   status / count                          - Ver quantidade de chunks e backend ativo │
│   exit / quit                             - Sair da sessão                           │
╰──────────────────────────────────────────────────────────────────────────────────────╯

rag-cli> ingest docs/pt-br/visao-geral-e-unidades.md
✓ Ingestão concluída: 7 chunks de visao-geral-e-unidades.md (Total: 7)

rag-cli> status
Backend ativo: PGVECTOR | Chunks indexados: 7

rag-cli> ask Quais são as unidades disponíveis e quais os diferenciais da unidade Jardins?
╭──────────────────────────────── Resposta do Assistente ────────────────────────────────╮
│ As unidades disponíveis são Central Imperial, Jardins Prime e Studio Femme.           │
│ A unidade Jardins Prime oferece atendimento VIP com lounge de degustação...           │
╰────────────────────── Backend: PGVECTOR | Fontes: 4 ──────────────────────────────────╯

rag-cli> quit
Encerrando sessão interativa...
```

#### ⚡ Direct Single Commands

- **Ingest a document file:**

  ```bash
  uv run python -m src.presentation.cli ingest --file docs/pt-br/visao-geral-e-unidades.md
  # or with explicit backend:
  uv run python -m src.presentation.cli ingest -f docs/pt-br/visao-geral-e-unidades.md -b pgvector
  ```

- **Ingest text directly:**

  ```bash
  uv run python -m src.presentation.cli ingest --text "A Barbearia Imperial foi fundada em 2018." --source "historia.txt"
  ```

- **Ask a question:**

  ```bash
  uv run python -m src.presentation.cli ask "Quais os horários de funcionamento?"
  # or with explicit backend:
  uv run python -m src.presentation.cli ask "Quais os horários de funcionamento?" -b pgvector
  ```

- **Display help:**

  ```bash
  uv run python -m src.presentation.cli --help
  ```

---

### 2. Web API (FastAPI) & Interactive Web UI

The asynchronous FastAPI service exposes OpenAPI-compliant endpoints and serves a local interactive chat UI.

![FastAPI Server Demo](docs/assets/demo-api.gif)

#### 🌐 Start the Development Server

```bash
uv run fastapi dev
```

The application will listen on `http://127.0.0.1:8000`.

- **Interactive Web Chat UI:** Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser:
  - Choose between **Português (`pt-br`)** and **English (`en`)**.
  - Click **Carregar Documentos** to trigger batch ingestion of all markdown files in the selected language directory.
  - Ask questions in natural language and receive grounded answers displaying retrieved source excerpts and similarity scores.

| 📥 Ingestão de Documentos | 💬 Chat Interativo |
| :---: | :---: |
| ![Web UI Ingestion](docs/assets/demo-web-ui-01.png) | ![Web UI Chat](docs/assets/demo-web-ui-02.png) |

- **Swagger UI Documentation:** Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
- **ReDoc Documentation:** Open [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc).

| 📖 Documentação Swagger | 🔍 Detalhes dos Endpoints | 🧪 Execução de Consultas |
| :---: | :---: | :---: |
| ![Swagger UI Overview](docs/assets/demo-web-api-01.png) | ![Swagger Endpoints](docs/assets/demo-web-api-02.png) | ![Swagger Query Execution](docs/assets/demo-web-api-03.png) |

#### 🚀 Start in Production Mode

```bash
uv run fastapi run
```

---

## 📡 REST API Endpoints

| Method | Endpoint | Description | Sample Payload |
| --- | --- | --- | --- |
| `GET` | `/health` | Service readiness and health status | *None* |
| `POST` | `/documents/ingest` | Ingest and vectorize a single text document (idempotent by source) | `{"content": "Text...", "source": "doc.md"}` |
| `POST` | `/documents/ingest/by-language` | Batch ingest all markdown documents for a language directory | `{"language": "pt-br"}` |
| `POST` | `/query` | Semantic search and LLM context-grounded answer generation | `{"question": "Quais os preços dos serviços?", "top_k": 4}` |

---

## 🧪 Testing & Code Quality

Strict quality checks are enforced across the repository, covering Domain, Application, Infrastructure, and Presentation layers.

### Run the Test Suite

```bash
uv run pytest
```

> **Note:** Integration tests in `test_pgvector_integration.py` safely isolate their test records using scoped source deletions (`delete_by_source`), never truncating user data in the live database.

### Code Formatting & Linting

```bash
# Check and apply formatting (Ruff)
uv run ruff format .

# Static analysis and linting (Ruff)
uv run ruff check .
```

### Complete Pre-Commit Validation

```bash
uv run ruff format --check . && uv run ruff check . && uv run pytest
```

### Regenerate SDD Models (OpenAPI)

When updating [openapi.yaml](openapi.yaml), regenerate the domain models:

```bash
uv run datamodel-codegen --input openapi.yaml --output src/domain/models/schemas.py --input-file-type openapi --output-model-type pydantic_v2.BaseModel
```

---

## 📝 Commit Conventions

All commits strictly follow **Conventional Commits** integrated with **Gitmoji**:

- ✨ `feat:` A new feature (e.g. `feat(cli): display active vector backend in panels`)
- 🐛 `fix:` A bug fix (e.g. `fix(pgvector): cast query embedding to vector in cosine distance`)
- 📝 `docs:` Documentation changes (e.g. `docs: update README with pgvector details`)
- ♻️ `refactor:` Code changes without functional differences
- ✅ `test:` Adding or updating unit/integration tests
- 🔧 `chore:` Build scripts, dependencies, or configuration

---

## 📄 License

This project is open-source software licensed under the [MIT License](LICENSE).
