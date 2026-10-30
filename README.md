# 🧠 Local RAG CLI & Web API

Aplicação modular de **RAG (Retrieval-Augmented Generation) 100% Local, Privada e Segura**, desenvolvida em Python segundo os princípios de **Clean Architecture**, **Domain-Driven Design (DDD)**, **SOLID** e **Spec-Driven Design (SDD)**.

---

## 📌 Visão Geral

O projeto implementa uma solução completa de busca semântica e geração de respostas aumentadas por contexto utilizando modelos locais através do **Ollama** e vetores com **Cosine Similarity** em memória e suporte a **pgvector**.

### ✨ Principais Características

- **100% Local & Seguro:** Sem dependência de APIs externas de LLMs (como OpenAI ou Anthropic); seus dados nunca saem da sua máquina.
- **Sem Frameworks Opacos:** Sem LangChain ou LlamaIndex. Orquestração, construção de prompts e estratégias de chunking implementadas manualmente com total controle e transparência.
- **Spec-Driven Design (SDD):** Contratos definidos estritamente em [openapi.yaml](openapi.yaml) como única fonte da verdade, com modelos Pydantic gerados automaticamente via `datamodel-code-generator`.
- **Apresentação Dupla (CLI & Web API):**
  - **CLI Interativo & Linha de Comando:** Interface de terminal moderna construída com **Typer** e **Rich**.
  - **REST API & Web UI Interativa:** Servidor assíncrono construído com **FastAPI**, documentação Swagger automática e interface de chat via navegador sem dependências externas.
- **Ingestão em Lote por Idioma:** Opção de ingestão automática de todos os documentos markdown organizados por pasta de idioma (`docs/<language>/*.md`).
- **Base de Conhecimento Bilíngue de Exemplo:** Exemplos práticos em português (`docs/pt-br/`) e inglês (`docs/en/`) sobre uma rede de barbearias com diferentes unidades e serviços.

---

## 🏛️ Arquitetura do Software

A aplicação segue rigorosamente as fronteiras concêntricas da **Clean Architecture**:

```text
Presentation (CLI / Typer, REST API & Web UI / FastAPI)
     ↓
Application (Use Cases: Ingestão, Consulta Semântica, Batch por Idioma)
     ↓
Domain (Entities, Protocols, Modelos SDD OpenAPI)
     ↑
Infrastructure (Ollama via HTTPX, Repositório Vetorial em Memória / PgVector via Psycopg)
```

### 📂 Estrutura de Diretórios

```text
rag_project/
├── openapi.yaml                 # Contrato da API (Single Source of Truth)
├── pyproject.toml               # Dependências e ferramentas gerenciadas com uv
├── compose.yaml                 # Infraestrutura Docker (Ollama + PgVector)
├── .env.example                 # Modelo de variáveis de ambiente
├── docs/                        # Base de conhecimento de exemplo (pt-br e en)
│   ├── pt-br/                   # Documentos em Português
│   └── en/                      # Documentos em Inglês
├── src/
│   ├── config/                  # Configurações centralizadas com pydantic-settings
│   ├── domain/                  # Núcleo de domínio (Entities, Interfaces e Modelos SDD)
│   │   ├── entities/            # Entidade DocumentChunk
│   │   ├── interfaces/          # Protocolos (Gateways de Embeddings, LLM e Repositório)
│   │   └── models/              # Modelos Pydantic gerados a partir do openapi.yaml
│   ├── application/             # Casos de uso da orquestração RAG
│   │   └── use_cases/           # Ingestão individual, busca semântica e batch por idioma
│   ├── infra/                   # Adaptadores de infraestrutura
│   │   └── adapters/            # OllamaAdapter (HTTPX sync/async), InMemoryVectorAdapter
│   └── presentation/            # Camada de apresentação
│       ├── cli/                 # Interface Typer (comandos pontuais e modo interativo)
│       └── api/                 # Web API FastAPI e interface gráfica de chat
└── tests/                       # Suíte de testes segregada espelhando o src/
    ├── domain/                  # Testes de entidades e contratos de domínio
    ├── infra/                   # Testes de adaptadores com mocks HTTP
    ├── application/             # Testes unitários dos use cases
    └── presentation/            # Testes ponta a ponta do CLI e API FastAPI
```

---

## 📋 Pré-requisitos

- **Python:** `>= 3.15`
- **Gerenciador de Pacotes:** [uv](https://github.com/astral-sh/uv) (rápido e determinístico)
- **Ollama:** Instalado localmente ou executado via Docker com os modelos:
  - `nomic-embed-text` (geração de embeddings com 768 dimensões)
  - `qwen3:4b-instruct` (modelo LLM instruct para respostas contextualizadas)
- **Docker & Docker Compose** (opcional, para rodar a stack completa)

---

## 🚀 Instalação e Configuração

### 1. Clonar o Repositório

```bash
git clone <url-do-repositorio>
cd rag-cli
```

### 2. Configurar o Ambiente

Copie o template de variáveis de ambiente:

```bash
cp .env.example .env
```

Edite o arquivo `.env` se necessário. Por padrão, ele vem configurado para:

```dotenv
PG_DSN=postgresql://dev:dev@localhost:5432/rag_db
OLLAMA_BASE_URL=http://localhost:11434/api
EMBED_MODEL=nomic-embed-text:latest
CHAT_MODEL=qwen3:4b-instruct
```

### 3. Instalar Dependências

Utilizando o `uv`:

```bash
uv sync
```

### 4. Inicializar os Modelos no Ollama

Se você já tiver o Ollama instalado no sistema operacional:

```bash
ollama pull nomic-embed-text
ollama pull qwen3:4b-instruct
```

Ou, alternativamente, inicie os serviços via Docker Compose (que já baixa os modelos automaticamente):

```bash
docker compose up -d
```

---

## 💻 Como Executar

### 1. Modo CLI (Linha de Comando)

O CLI oferece modo interativo com sessão contínua na memória ou execução de comandos diretos.

#### 💬 Modo Interativo (Recomendado para testes no terminal)

Permite carregar documentos e fazer perguntas sequenciais mantendo os chunks indexados:

```bash
uv run python -m src.presentation.cli interactive
```

Dentro da sessão interativa:

```text
rag-cli> ingest docs/pt-br/visao-geral-e-unidades.md
✓ Ingestão concluída com sucesso: 7 chunks indexados de visao-geral-e-unidades.md (Total: 7)

rag-cli> ingest docs/pt-br/servicos-e-precos.md
✓ Ingestão concluída com sucesso: 6 chunks indexados de servicos-e-precos.md (Total: 13)

rag-cli> ask Qual unidade é exclusiva para mulheres e quais serviços ela oferece?
Resposta:
A unidade exclusiva para o público feminino é o Studio Femme, que oferece serviços especializados...

rag-cli> status
Chunks indexados: 13

rag-cli> exit
```

#### ⚡ Comandos Diretos da CLI

- **Ingestão direta de texto:**

  ```bash
  uv run python -m src.presentation.cli ingest --text "A Barbearia Imperial foi fundada em 2018." --source "historia.txt"
  ```

- **Ingestão de arquivo:**

  ```bash
  uv run python -m src.presentation.cli ingest --file docs/pt-br/visao-geral-e-unidades.md
  ```

- **Fazer uma pergunta pontual:**

  ```bash
  uv run python -m src.presentation.cli ask "Quais são as unidades disponíveis?"
  ```

- **Acessar a ajuda dos comandos:**

  ```bash
  uv run python -m src.presentation.cli --help
  ```

---

### 2. Modo Web API (FastAPI) & Interface Gráfica

A API assíncrona permite integrar o RAG a serviços externos ou interagir diretamente via navegador.

#### 🌐 Iniciar o Servidor de Desenvolvimento

```bash
uv run fastapi dev
```

> O servidor iniciará em `http://127.0.0.1:8000`.

- **Interface Gráfica de Chat:** Acesse [http://127.0.0.1:8000/](http://127.0.0.1:8000/) no seu navegador.
  - Selecione o idioma desejado (`pt-br` ou `en`) e clique em **Carregar Documentos** para indexar em lote todos os arquivos da pasta correspondente (`docs/<language>`).
  - Digite sua pergunta no console de chat para obter a resposta gerada com as fontes e escores de similaridade associados.
- **Documentação Interativa Swagger (OpenAPI):** Acesse [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
- **Documentação ReDoc:** Acesse [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc).

#### 🚀 Iniciar em Modo Produção

```bash
uv run fastapi run
```

---

## 📡 Endpoints da API REST

| Método | Endpoint | Descrição | Exemplo de Payload |
| --- | --- | --- | --- |
| `GET` | `/health` | Checagem de integridade e versão da API | *Nenhum* |
| `POST` | `/documents/ingest` | Ingestão e vetorização de texto individual | `{"content": "Texto...", "source": "doc.md"}` |
| `POST` | `/documents/ingest/by-language` | Ingestão em lote de todos os arquivos de um idioma | `{"language": "pt-br"}` |
| `POST` | `/query` | Busca semântica e geração de resposta com LLM | `{"question": "Qual é o preço do corte?", "top_k": 4}` |

---

## 🧪 Qualidade de Código e Testes

O projeto adota padrões rígidos de qualidade:

### Execução dos Testes

A suíte de testes cobre testes de contratos de domínio, adaptadores, use cases e integrações ponta a ponta (E2E) para CLI e ASGI:

```bash
uv run pytest
```

### Formatação de Código

```bash
uv run ruff format .
```

### Análise Estática (Linter)

```bash
uv run ruff check .
```

### Verificação Completa Pré-Commit

```bash
uv run ruff format --check . && uv run ruff check . && uv run pytest
```

### Regeneração de Modelos SDD (OpenAPI)

Se o contrato [openapi.yaml](openapi.yaml) for alterado, regenere os modelos Pydantic com:

```bash
uv run datamodel-codegen --input openapi.yaml --output src/domain/models/schemas.py --input-file-type openapi --output-model-type pydantic_v2.BaseModel
```

---

## 📝 Padrão de Commits

Todos os commits devem seguir a convenção de **Conventional Commits** e **Gitmoji**:

- ✨ `feat:` Novas funcionalidades (ex: `feat(api): add batch language ingest endpoint`)
- 🐛 `fix:` Correção de bugs
- 📝 `docs:` Atualizações na documentação ou contratos
- ♻️ `refactor:` Refatoração de código sem alteração funcional
- ✅ `test:` Criação ou ajuste de testes
- 🔧 `chore:` Atualizações de build, dependências ou ferramentas

---

## 📄 Licença

Este projeto é desenvolvido para fins de portfólio e estudos arquiteturais avançados de RAG Local em Python. Sinta-se livre para utilizar e estender conforme necessário.
