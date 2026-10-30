import socket

import pytest

from src.config.settings import settings
from src.domain.entities import DocumentChunk
from src.infra.adapters.pgvector_repository import PgVectorAdapter


def is_postgres_available() -> bool:
    """Check if PostgreSQL port is open and accessible."""
    try:
        with socket.create_connection(("localhost", 5432), timeout=0.5):
            return True
    except OSError:
        return False


@pytest.mark.skipif(
    not is_postgres_available(),
    reason="Live PostgreSQL/pgvector container is not running.",
)
def test_pgvector_live_integration_lifecycle():
    """
    Live integration test against pgvector running in Docker.
    Tests table creation, vector insertion, cosine distance similarity,
    count, and table truncation.
    """
    adapter = PgVectorAdapter(conn_str=settings.pg_dsn, auto_init=True)
    adapter.clear()

    # nomic-embed-text uses 768 dimensions
    vec_a = [0.0] * 768
    vec_a[0] = 1.0  # Identical direction to query

    vec_b = [0.0] * 768
    vec_b[1] = 1.0  # Orthogonal direction

    chunk_a = DocumentChunk(
        content="Chunk A: Highly relevant",
        embedding=vec_a,
        source="test_live.md",
    )
    chunk_b = DocumentChunk(
        content="Chunk B: Less relevant",
        embedding=vec_b,
        source="test_live.md",
    )

    adapter.save_chunks([chunk_a, chunk_b])
    assert adapter.count() == 2

    query_vec = [0.0] * 768
    query_vec[0] = 1.0

    results = adapter.search_similar(query_embedding=query_vec, top_k=2)
    assert len(results) == 2

    top_chunk, top_score = results[0]
    second_chunk, second_score = results[1]

    # vec_a is collinear with query_vec -> cosine similarity == 1.0
    assert top_chunk.content == "Chunk A: Highly relevant"
    assert round(top_score, 3) == 1.000

    # vec_b is orthogonal -> cosine similarity == 0.0
    assert second_chunk.content == "Chunk B: Less relevant"
    assert round(second_score, 3) == 0.000

    adapter.clear()
    assert adapter.count() == 0


@pytest.mark.anyio
@pytest.mark.skipif(
    not is_postgres_available(),
    reason="Live PostgreSQL/pgvector container is not running.",
)
async def test_pgvector_live_async_integration_lifecycle():
    """
    Live asynchronous integration test against pgvector running in Docker.
    Tests asave_chunks, asearch_similar, acount, and aclear.
    """
    adapter = PgVectorAdapter(conn_str=settings.pg_dsn, auto_init=False)
    await adapter.aclear()

    vec_a = [0.0] * 768
    vec_a[0] = 1.0

    vec_b = [0.0] * 768
    vec_b[1] = 1.0

    chunks = [
        DocumentChunk(
            content="Async Chunk A",
            embedding=vec_a,
            source="async_test.md",
        ),
        DocumentChunk(
            content="Async Chunk B",
            embedding=vec_b,
            source="async_test.md",
        ),
    ]

    await adapter.asave_chunks(chunks)
    assert await adapter.acount() == 2

    query_vec = [0.0] * 768
    query_vec[0] = 1.0

    results = await adapter.asearch_similar(query_embedding=query_vec, top_k=1)
    assert len(results) == 1
    assert results[0][0].content == "Async Chunk A"
    assert round(results[0][1], 3) == 1.000

    await adapter.aclear()
    assert await adapter.acount() == 0
