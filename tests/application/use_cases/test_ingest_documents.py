import pytest

from src.application.use_cases.ingest_documents import (
    IngestDocumentsUseCase,
    chunk_text,
)
from src.domain.entities import DocumentChunk
from src.domain.models import IngestRequest


class FakeEmbeddingGateway:
    def generate_embedding(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


class FakeVectorRepository:
    def __init__(self) -> None:
        self.chunks: list[DocumentChunk] = []

    def save_chunks(self, chunks: list[DocumentChunk]) -> None:
        self.chunks.extend(chunks)

    def search_similar(
        self, query_embedding: list[float], top_k: int = 3
    ) -> list[tuple[DocumentChunk, float]]:
        return [(c, 0.95) for c in self.chunks[:top_k]]


def test_chunk_text():
    text = "Word " * 150  # ~750 chars
    chunks = chunk_text(text, chunk_size=300, chunk_overlap=30)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c) <= 350


def test_ingest_documents_use_case_success():
    embedder = FakeEmbeddingGateway()
    repo = FakeVectorRepository()
    use_case = IngestDocumentsUseCase(embedder, repo, chunk_size=100)

    request = IngestRequest(
        content="This is a test document with sufficient words to verify ingestion.",
        source="doc1.txt",
        metadata={"category": "test"},
    )
    response = use_case.execute(request)

    assert response.status == "success"
    assert response.chunks_count >= 1
    assert len(repo.chunks) == response.chunks_count
    assert repo.chunks[0].source == "doc1.txt"


def test_ingest_documents_use_case_empty_validation():
    embedder = FakeEmbeddingGateway()
    repo = FakeVectorRepository()
    use_case = IngestDocumentsUseCase(embedder, repo)

    with pytest.raises(ValueError, match="cannot be empty"):
        use_case.execute(IngestRequest(content="   "))
