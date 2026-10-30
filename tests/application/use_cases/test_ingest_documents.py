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

    def delete_by_source(self, source: str) -> None:
        self.chunks = [c for c in self.chunks if c.source != source]

    def delete_by_metadata(self, key: str, value: object) -> None:
        self.chunks = [c for c in self.chunks if c.metadata.get(key) != value]


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


@pytest.mark.anyio
async def test_ingest_documents_use_case_async():
    class FakeAsyncEmbedder:
        async def agenerate_embeddings(self, texts: list[str]) -> list[list[float]]:
            return [[0.1, 0.2, 0.3] for _ in texts]

    class FakeAsyncRepo:
        def __init__(self) -> None:
            self.chunks: list[DocumentChunk] = []

        async def asave_chunks(self, chunks: list[DocumentChunk]) -> None:
            self.chunks.extend(chunks)

        async def adelete_by_source(self, source: str) -> None:
            self.chunks = [c for c in self.chunks if c.source != source]

    embedder = FakeAsyncEmbedder()
    repo = FakeAsyncRepo()
    use_case = IngestDocumentsUseCase(embedder, repo, chunk_size=100)

    request = IngestRequest(
        content="This is an async test document for ingestion.",
        source="async_doc.txt",
    )
    response = await use_case.aexecute(request)

    assert response.status == "success"
    assert response.chunks_count >= 1
    assert len(repo.chunks) == response.chunks_count


def test_ingest_documents_reingest_replaces_source():
    embedder = FakeEmbeddingGateway()
    repo = FakeVectorRepository()
    use_case = IngestDocumentsUseCase(embedder, repo, chunk_size=100)

    req1 = IngestRequest(content="Version 1 content", source="file.txt")
    res1 = use_case.execute(req1)
    assert len(repo.chunks) == res1.chunks_count

    req2 = IngestRequest(content="Version 2 updated content", source="file.txt")
    res2 = use_case.execute(req2)
    assert len(repo.chunks) == res2.chunks_count
    assert repo.chunks[0].content == "Version 2 updated content"
