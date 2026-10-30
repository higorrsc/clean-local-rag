import httpx
import pytest

from src.infra.adapters.in_memory_repository import InMemoryVectorAdapter
from src.presentation.api.dependencies import (
    get_ollama_adapter,
    get_vector_repository,
)
from src.presentation.api.main import app


class DynamicOllamaMock:
    """Mock simulating Ollama async embedding and chat responses."""

    async def agenerate_embedding(self, text: str) -> list[float]:
        return [0.2, 0.4, 0.6]

    async def agenerate_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [[0.2, 0.4, 0.6] for _ in texts]

    async def agenerate_response(
        self, prompt: str, system_prompt: str | None = None
    ) -> str:
        if "Studio Femme" in prompt or "mulheres" in prompt.lower():
            return (
                "A unidade exclusiva para o público feminino é a Unidade Studio Femme."
            )
        elif "prices" in prompt.lower() or "services" in prompt.lower():
            return (
                "We offer premium grooming services including haircut and beard trim."
            )
        return "Resposta baseada no contexto fornecido."

    async def aclose(self) -> None:
        pass


@pytest.mark.anyio
async def test_api_e2e_batch_ingest_and_query_pt_br():
    shared_repo = InMemoryVectorAdapter()
    mock_ollama = DynamicOllamaMock()

    app.dependency_overrides[get_vector_repository] = lambda: shared_repo
    app.dependency_overrides[get_ollama_adapter] = lambda: mock_ollama

    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # 1. Health check
            health_res = await client.get("/health")
            assert health_res.status_code == 200
            assert health_res.json()["status"] == "ok"

            # 2. Batch Ingest Portuguese documents
            ingest_res = await client.post(
                "/documents/ingest/by-language",
                json={"language": "pt-br"},
            )
            assert ingest_res.status_code == 200
            ingest_data = ingest_res.json()
            assert ingest_data["status"] == "success"
            assert ingest_data["language"] == "pt-br"
            assert ingest_data["files_count"] == 3
            assert ingest_data["chunks_count"] >= 3
            assert shared_repo.count() == ingest_data["chunks_count"]

            # 3. Query knowledge base
            query_res = await client.post(
                "/query",
                json={
                    "question": "Qual unidade é exclusiva para mulheres?",
                    "top_k": 4,
                },
            )
            assert query_res.status_code == 200
            query_data = query_res.json()
            assert (
                "Studio Femme" in query_data["answer"]
                or "feminino" in query_data["answer"]
            )
            assert len(query_data["sources"]) >= 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_api_e2e_batch_ingest_and_query_en():
    shared_repo = InMemoryVectorAdapter()
    mock_ollama = DynamicOllamaMock()

    app.dependency_overrides[get_vector_repository] = lambda: shared_repo
    app.dependency_overrides[get_ollama_adapter] = lambda: mock_ollama

    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # 1. Batch Ingest English documents
            ingest_res = await client.post(
                "/documents/ingest/by-language",
                json={"language": "en"},
            )
            assert ingest_res.status_code == 200
            ingest_data = ingest_res.json()
            assert ingest_data["status"] == "success"
            assert ingest_data["language"] == "en"
            assert ingest_data["files_count"] == 3
            assert ingest_data["chunks_count"] >= 3

            # 2. Query knowledge base in English
            query_res = await client.post(
                "/query",
                json={
                    "question": "What services and prices are available?",
                    "top_k": 4,
                },
            )
            assert query_res.status_code == 200
            query_data = query_res.json()
            assert len(query_data["sources"]) >= 1
    finally:
        app.dependency_overrides.clear()
