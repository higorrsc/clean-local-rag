.PHONY: help up down pull-models cli api ingest test lint format check status

# Default target when running 'make'
.DEFAULT_GOAL := help

help: ## Display the list of available commands
	@echo "=========================================================="
	@echo "          🧠 Clean Local RAG - Project Management"
	@echo "=========================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

up: ## Start infrastructure (Postgres only if local Ollama exists, or full Docker stack)
	@bash scripts/setup-infra.sh

down: ## Stop and remove Docker Compose containers
	@docker compose down

pull-models: ## Pull required models (nomic-embed-text and qwen3:4b-instruct) in local Ollama
	@bash scripts/pull-models.sh

cli: ## Launch interactive CLI terminal session
	@uv run python -m src.presentation.cli interactive

api: ## Launch FastAPI development server (Swagger at /docs and Chat UI at /)
	@uv run fastapi dev

ingest: ## Ingest sample document into the active vector repository
	@uv run python -m src.presentation.cli ingest -f docs/pt-br/visao-geral-e-unidades.md

test: ## Run unit and integration test suite
	@uv run python -m pytest

lint: ## Run ruff linter
	@uv run ruff check .

format: ## Format codebase with ruff
	@uv run ruff format .

check: lint test ## Run lint and test suite sequentially

status: ## Show status of Docker containers and local Ollama models
	@echo "\033[1;36m=== Docker Containers ===\033[0m"
	@docker compose ps
	@echo ""
	@if command -v ollama >/dev/null 2>&1; then \
		echo "\033[1;36m=== Local Ollama Models ===\033[0m"; \
		ollama list 2>/dev/null || echo "Local Ollama is not responding."; \
	fi
