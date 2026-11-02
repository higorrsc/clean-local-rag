#!/usr/bin/env bash
set -euo pipefail

# Text formatting
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
CYAN="\033[0;36m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BOLD}${CYAN}=== Local RAG Infrastructure Orchestrator ===${RESET}"

# Load environment variables if .env exists
if [ -f .env ]; then
  EMBED_MODEL="${EMBED_MODEL:-$(grep -E '^EMBED_MODEL=' .env | cut -d '=' -f2- | tr -d '\"\r' || true)}"
  CHAT_MODEL="${CHAT_MODEL:-$(grep -E '^CHAT_MODEL=' .env | cut -d '=' -f2- | tr -d '\"\r' || true)}"
fi

EMBED_MODEL="${EMBED_MODEL:-nomic-embed-text:latest}"
CHAT_MODEL="${CHAT_MODEL:-qwen3:4b-instruct}"

# Helper function to check if a model exists in local ollama
has_local_model() {
  local target="$1"
  local base="${target%:latest}"
  ollama list 2>/dev/null | awk '{print $1}' | grep -E "^(${target}|${base}(:latest)?)$" >/dev/null 2>&1
}

# Check if local Ollama binary exists on host
if command -v ollama >/dev/null 2>&1; then
  echo -e "${GREEN}✓ Local Ollama detected on host.${RESET}"
  echo -e "${CYAN}→ Starting database service only (PostgreSQL + pgvector)...${RESET}"
  docker compose up -d postgres

  # Check if Ollama daemon is reachable
  if ollama list >/dev/null 2>&1; then
    missing_models=()

    if ! has_local_model "$EMBED_MODEL"; then
      missing_models+=("$EMBED_MODEL")
    fi

    if ! has_local_model "$CHAT_MODEL"; then
      missing_models+=("$CHAT_MODEL")
    fi

    if [ ${#missing_models[@]} -gt 0 ]; then
      echo ""
      echo -e "${YELLOW}${BOLD}[WARNING] Required models not found in local Ollama:${RESET}"
      for model in "${missing_models[@]}"; do
        echo -e "  ${RED}✗ ${model}${RESET}"
      done
      echo ""
      echo -e "${YELLOW}Please pull the required models by running:${RESET}"
      echo -e "  ${BOLD}make pull-models${RESET}  ${CYAN}(or ./scripts/pull-models.sh)${RESET}"
      echo ""
    else
      echo -e "${GREEN}✓ Required models verified in local Ollama:${RESET}"
      echo -e "  • Embedding: ${CYAN}${EMBED_MODEL}${RESET}"
      echo -e "  • Chat/LLM:  ${CYAN}${CHAT_MODEL}${RESET}"
    fi
  else
    echo ""
    echo -e "${YELLOW}${BOLD}[WARNING] Ollama is installed, but the daemon is not running.${RESET}"
    echo -e "Make sure to start the local Ollama service:"
    echo -e "  ${BOLD}ollama serve${RESET}  (or ${BOLD}systemctl start ollama${RESET})"
    echo ""
  fi

else
  echo -e "${YELLOW}! Local Ollama not detected on host.${RESET}"
  echo -e "${CYAN}→ Starting full stack with Docker Compose (PostgreSQL + Ollama container + Auto-pull)...${RESET}"
  docker compose up -d

  echo ""
  echo -e "${GREEN}✓ Full stack started via Docker Compose.${RESET}"
  echo -e "The ${CYAN}rag_ollama_init${RESET} helper service will automatically pull models on first launch."
  echo -e "You can monitor the download progress with:"
  echo -e "  ${BOLD}docker logs -f rag_ollama_init${RESET}"
  echo ""
fi

echo -e "${GREEN}${BOLD}Ready! Infrastructure is operational.${RESET}"
