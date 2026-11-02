import httpx

from src.config.settings import settings
from src.domain.interfaces import (
    AsyncEmbeddingGateway,
    AsyncLLMGateway,
    EmbeddingGateway,
    LLMGateway,
)


class OllamaAdapter(
    EmbeddingGateway,
    LLMGateway,
    AsyncEmbeddingGateway,
    AsyncLLMGateway,
):
    """
    Adapter interfacing directly with local Ollama service using HTTPX.
    Implements sync and async gateways without external frameworks.
    """

    def __init__(
        self,
        base_url: str | None = None,
        embed_model: str | None = None,
        chat_model: str | None = None,
        client: httpx.Client | None = None,
        async_client: httpx.AsyncClient | None = None,
        timeout: float | None = None,
    ) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.embed_model = embed_model or settings.embed_model
        self.chat_model = chat_model or settings.chat_model
        req_timeout = timeout or settings.ollama_timeout
        self.client = client or httpx.Client(timeout=req_timeout)
        self.async_client = async_client or httpx.AsyncClient(timeout=req_timeout)

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for single text using /api/embed (or legacy /api/embeddings).
        """
        embeddings = self.generate_embeddings([text])
        if not embeddings:
            raise ValueError("Ollama returned an empty embedding list.")
        return embeddings[0]

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of texts using Ollama's /api/embed endpoint.
        """
        if not texts:
            return []

        # Try /api/embed (modern Ollama batch embedding endpoint)
        embed_url = f"{self.base_url}/embed"
        payload = {"model": self.embed_model, "input": texts}

        response = self.client.post(embed_url, json=payload)

        if response.status_code == 200:
            data = response.json()
            return data.get("embeddings", [])

        # Fallback to legacy /api/embeddings endpoint if /api/embed is unavailable
        legacy_url = f"{self.base_url}/embeddings"
        results: list[list[float]] = []
        for text in texts:
            res = self.client.post(
                legacy_url, json={"model": self.embed_model, "prompt": text}
            )
            res.raise_for_status()
            results.append(res.json().get("embedding", []))
        return results

    async def agenerate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for a single text asynchronously.
        """
        embeddings = await self.agenerate_embeddings([text])
        if not embeddings:
            raise ValueError("Ollama returned an empty embedding list.")
        return embeddings[0]

    async def agenerate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings asynchronously using Ollama's /api/embed endpoint.
        """
        if not texts:
            return []

        embed_url = f"{self.base_url}/embed"
        payload = {"model": self.embed_model, "input": texts}

        response = await self.async_client.post(embed_url, json=payload)

        if response.status_code == 200:
            data = response.json()
            return data.get("embeddings", [])

        legacy_url = f"{self.base_url}/embeddings"
        results: list[list[float]] = []
        for text in texts:
            res = await self.async_client.post(
                legacy_url, json={"model": self.embed_model, "prompt": text}
            )
            res.raise_for_status()
            results.append(res.json().get("embedding", []))
        return results

    def generate_response(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """
        Generate chat response using Ollama's /api/chat endpoint with stream=false.
        """
        chat_url = f"{self.base_url}/chat"
        messages: list[dict[str, str]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.chat_model,
            "messages": messages,
            "stream": False,
        }

        response = self.client.post(chat_url, json=payload)
        response.raise_for_status()

        data = response.json()
        message = data.get("message", {})
        return message.get("content", "")

    async def agenerate_response(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """
        Generate chat response asynchronously using Ollama's /api/chat endpoint.
        """
        chat_url = f"{self.base_url}/chat"
        messages: list[dict[str, str]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.chat_model,
            "messages": messages,
            "stream": False,
        }

        response = await self.async_client.post(chat_url, json=payload)
        response.raise_for_status()

        data = response.json()
        message = data.get("message", {})
        return message.get("content", "")

    def close(self) -> None:
        """Close synchronous client."""
        self.client.close()

    async def aclose(self) -> None:
        """Close asynchronous client."""
        await self.async_client.aclose()
