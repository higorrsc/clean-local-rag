import pytest

from src.domain.entities import DocumentChunk
from src.domain.interfaces import AsyncVectorRepository, VectorRepository
from src.infra.adapters.in_memory_repository import InMemoryVectorAdapter


def test_in_memory_adapter_implements_protocol():
    adapter = InMemoryVectorAdapter()
    assert isinstance(adapter, VectorRepository)
    assert isinstance(adapter, AsyncVectorRepository)


def test_empty_repository_returns_empty_results():
    adapter = InMemoryVectorAdapter()
    results = adapter.search_similar([1.0, 0.0, 0.0], top_k=3)
    assert results == []


def test_cosine_similarity_retrieval_ranking():
    adapter = InMemoryVectorAdapter()

    # Chunk A is perfectly aligned with [1.0, 0.0]
    chunk_a = DocumentChunk(content="Python programming", embedding=[1.0, 0.0])
    # Chunk B is at 45 degrees [1.0, 1.0]
    chunk_b = DocumentChunk(content="Data science", embedding=[1.0, 1.0])
    # Chunk C is orthogonal [0.0, 1.0]
    chunk_c = DocumentChunk(content="Baking cakes", embedding=[0.0, 1.0])

    adapter.save_chunks([chunk_a, chunk_b, chunk_c])
    assert adapter.count() == 3

    # Query aligned with [1.0, 0.0]
    results = adapter.search_similar([1.0, 0.0], top_k=2)

    assert len(results) == 2
    top_chunk, top_score = results[0]
    second_chunk, second_score = results[1]

    assert top_chunk.content == "Python programming"
    assert round(top_score, 4) == 1.0

    assert second_chunk.content == "Data science"
    assert top_score > second_score


@pytest.mark.anyio
async def test_async_in_memory_repository_operations():
    adapter = InMemoryVectorAdapter()
    chunk = DocumentChunk(content="Async chunk", embedding=[1.0, 0.0])

    await adapter.asave_chunks([chunk])
    assert adapter.count() == 1

    results = await adapter.asearch_similar([1.0, 0.0], top_k=1)
    assert len(results) == 1
    assert results[0][0].content == "Async chunk"
    assert round(results[0][1], 4) == 1.0
