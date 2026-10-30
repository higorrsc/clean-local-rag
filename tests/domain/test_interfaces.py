from src.domain.entities import DocumentChunk
from src.domain.interfaces import (
    AsyncEmbeddingGateway,
    AsyncLLMGateway,
    AsyncVectorRepository,
    EmbeddingGateway,
    LLMGateway,
    VectorRepository,
)


class FakeEmbedder:
    def generate_embedding(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


class FakeAsyncEmbedder:
    async def agenerate_embedding(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    async def agenerate_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


class FakeLLM:
    def generate_response(self, prompt: str, system_prompt: str | None = None) -> str:
        return "Fake answer"


class FakeAsyncLLM:
    async def agenerate_response(
        self, prompt: str, system_prompt: str | None = None
    ) -> str:
        return "Fake async answer"


class FakeRepo:
    def save_chunks(self, chunks: list[DocumentChunk]) -> None:
        pass

    def search_similar(
        self, query_embedding: list[float], top_k: int = 3
    ) -> list[tuple[DocumentChunk, float]]:
        return []

    def delete_by_source(self, source: str) -> None:
        pass

    def delete_by_metadata(self, key: str, value: object) -> None:
        pass


class FakeAsyncRepo:
    async def asave_chunks(self, chunks: list[DocumentChunk]) -> None:
        pass

    async def asearch_similar(
        self, query_embedding: list[float], top_k: int = 4
    ) -> list[tuple[DocumentChunk, float]]:
        return []

    async def adelete_by_source(self, source: str) -> None:
        pass

    async def adelete_by_metadata(self, key: str, value: object) -> None:
        pass


def test_protocols_runtime_checkable():
    assert isinstance(FakeEmbedder(), EmbeddingGateway)
    assert isinstance(FakeLLM(), LLMGateway)
    assert isinstance(FakeRepo(), VectorRepository)
    assert isinstance(FakeAsyncEmbedder(), AsyncEmbeddingGateway)
    assert isinstance(FakeAsyncLLM(), AsyncLLMGateway)
    assert isinstance(FakeAsyncRepo(), AsyncVectorRepository)
