#!/usr/bin/env bash
set -euo pipefail

# Text formatting
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
CYAN="\033[0;36m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BOLD}${CYAN}=== Pull Models for Local Ollama ===${RESET}"

if ! command -v ollama >/dev/null 2>&1; then
  echo -e "${RED}Error: 'ollama' binary was not found in PATH.${RESET}"
  echo "Install Ollama from https://ollama.com or use the Docker Compose container."
  exit 1
fi

# Load environment variables if .env exists
if [ -f .env ]; then
  EMBED_MODEL="${EMBED_MODEL:-$(grep -E '^EMBED_MODEL=' .env | cut -d '=' -f2- | tr -d '\"\r' || true)}"
  CHAT_MODEL="${CHAT_MODEL:-$(grep -E '^CHAT_MODEL=' .env | cut -d '=' -f2- | tr -d '\"\r' || true)}"
fi

EMBED_MODEL="${EMBED_MODEL:-nomic-embed-text:latest}"
CHAT_MODEL="${CHAT_MODEL:-qwen3:4b-instruct}"

echo -e "${CYAN}1/2 Pulling embedding model (${EMBED_MODEL})...${RESET}"
ollama pull "$EMBED_MODEL"

echo ""
echo -e "${CYAN}2/2 Pulling chat model (${CHAT_MODEL})...${RESET}"
ollama pull "$CHAT_MODEL"

echo ""
echo -e "${GREEN}${BOLD}✓ All required models pulled successfully into local Ollama!${RESET}"
