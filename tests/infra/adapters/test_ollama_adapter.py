import httpx

from src.domain.interfaces import EmbeddingGateway, LLMGateway
from src.infra.adapters.ollama import OllamaAdapter


def test_ollama_adapter_implements_protocols():
    adapter = OllamaAdapter()
    assert isinstance(adapter, EmbeddingGateway)
    assert isinstance(adapter, LLMGateway)


def test_generate_embeddings_modern_endpoint():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/embed"
        content = request.read().decode("utf-8")
        assert "nomic-embed-text" in content
        return httpx.Response(
            200,
            json={
                "model": "nomic-embed-text:latest",
                "embeddings": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = OllamaAdapter(client=client)

    embeddings = adapter.generate_embeddings(["chunk 1", "chunk 2"])
    assert len(embeddings) == 2
    assert embeddings[0] == [0.1, 0.2, 0.3]
    assert embeddings[1] == [0.4, 0.5, 0.6]

    single = adapter.generate_embedding("chunk 1")
    assert single == [0.1, 0.2, 0.3]


def test_generate_embeddings_legacy_fallback():
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if request.url.path == "/api/embed":
            return httpx.Response(404)
        elif request.url.path == "/api/embeddings":
            return httpx.Response(200, json={"embedding": [0.7, 0.8, 0.9]})
        return httpx.Response(400)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = OllamaAdapter(client=client)

    embeddings = adapter.generate_embeddings(["test"])
    assert embeddings == [[0.7, 0.8, 0.9]]


def test_generate_response_chat_endpoint():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        content = request.read().decode("utf-8")
        assert "qwen3:4b-instruct" in content
        assert "What is RAG?" in content
        return httpx.Response(
            200,
            json={
                "model": "qwen3:4b-instruct",
                "message": {
                    "role": "assistant",
                    "content": "RAG stands for Retrieval-Augmented Generation.",
                },
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = OllamaAdapter(client=client)

    answer = adapter.generate_response(
        prompt="What is RAG?",
        system_prompt="You are a helpful RAG assistant.",
    )
    assert answer == "RAG stands for Retrieval-Augmented Generation."
