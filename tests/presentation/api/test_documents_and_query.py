from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from src.domain.entities import DocumentChunk
from src.infra.adapters.in_memory_repository import InMemoryVectorAdapter
from src.presentation.api.dependencies import (
    get_ollama_adapter,
    get_vector_repository,
)
from src.presentation.api.main import app


class MockOllamaAdapter:
    async def agenerate_embedding(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    async def agenerate_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]

    async def agenerate_response(
        self, prompt: str, system_prompt: str | None = None
    ) -> str:
        return "Unidade Studio Femme é a unidade feminina."

    async def aclose(self) -> None:
        pass


@pytest.fixture
def test_setup() -> Generator[tuple[TestClient, InMemoryVectorAdapter]]:
    mock_repo = InMemoryVectorAdapter()
    mock_ollama = MockOllamaAdapter()

    app.dependency_overrides[get_vector_repository] = lambda: mock_repo
    app.dependency_overrides[get_ollama_adapter] = lambda: mock_ollama

    with TestClient(app) as client:
        yield client, mock_repo

    app.dependency_overrides.clear()


def test_ingest_document_single(test_setup):
    client, repo = test_setup
    payload = {"content": "Documento de teste", "source": "test.md"}
    response = client.post("/documents/ingest", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["chunks_count"] == 1
    assert repo.count() == 1


def test_ingest_document_single_empty_validation(test_setup):
    client, _ = test_setup
    payload = {"content": "   "}
    response = client.post("/documents/ingest", json=payload)
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]


def test_batch_ingest_by_language_pt_br(test_setup):
    client, repo = test_setup
    payload = {"language": "pt-br"}
    response = client.post("/documents/ingest/by-language", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["language"] == "pt-br"
    assert data["files_count"] >= 3
    assert data["chunks_count"] >= 3
    assert "visao-geral-e-unidades.md" in data["documents"]
    assert repo.count() >= 3


def test_batch_ingest_by_language_not_found(test_setup):
    client, _ = test_setup
    payload = {"language": "non-existent-lang"}
    response = client.post("/documents/ingest/by-language", json=payload)
    assert response.status_code == 404


def test_query_knowledge_base(test_setup):
    client, repo = test_setup
    chunk = DocumentChunk(
        content="Unidade Studio Femme é dedicada exclusivamente ao público feminino.",
        embedding=[0.1, 0.2, 0.3],
        source="visao-geral-e-unidades.md",
    )
    repo.save_chunks([chunk])

    payload = {
        "question": "Qual unidade é exclusiva para mulheres?",
        "top_k": 3,
    }
    response = client.post("/query", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Unidade Studio Femme é a unidade feminina."
    assert len(data["sources"]) == 1
    assert data["sources"][0]["source"] == "visao-geral-e-unidades.md"


def test_query_empty_question_validation(test_setup):
    client, _ = test_setup
    payload = {"question": "   "}
    response = client.post("/query", json=payload)
    assert response.status_code == 400
