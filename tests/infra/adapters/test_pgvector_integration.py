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
    and scoped source deletion.
    """
    adapter = PgVectorAdapter(conn_str=settings.pg_dsn, auto_init=True)
    adapter.delete_by_source("test_live.md")
    initial_count = adapter.count()

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
    assert adapter.count() == initial_count + 2

    query_vec = [0.0] * 768
    query_vec[0] = 1.0

    results = adapter.search_similar(query_embedding=query_vec, top_k=2)
    assert len(results) >= 2

    top_chunk, top_score = results[0]

    # vec_a is collinear with query_vec -> cosine similarity == 1.0
    assert top_chunk.content == "Chunk A: Highly relevant"
    assert round(top_score, 3) == 1.000

    adapter.delete_by_source("test_live.md")
    assert adapter.count() == initial_count


@pytest.mark.anyio
@pytest.mark.skipif(
    not is_postgres_available(),
    reason="Live PostgreSQL/pgvector container is not running.",
)
async def test_pgvector_live_async_integration_lifecycle():
    """
    Live asynchronous integration test against pgvector running in Docker.
    Tests asave_chunks, asearch_similar, and adelete_by_source.
    """
    adapter = PgVectorAdapter(conn_str=settings.pg_dsn, auto_init=False)
    await adapter.adelete_by_source("async_test.md")
    initial_count = await adapter.acount()

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
    assert await adapter.acount() == initial_count + 2

    query_vec = [0.0] * 768
    query_vec[0] = 1.0

    results = await adapter.asearch_similar(query_embedding=query_vec, top_k=1)
    assert len(results) >= 1
    assert results[0][0].content == "Async Chunk A"
    assert round(results[0][1], 3) == 1.000

    await adapter.adelete_by_source("async_test.md")
    assert await adapter.acount() == initial_count


@pytest.mark.skipif(
    not is_postgres_available(),
    reason="Live PostgreSQL/pgvector container is not running.",
)
def test_pgvector_live_delete_by_source_and_metadata():
    """
    Verify live deletion by source and metadata key in pgvector.
    """
    adapter = PgVectorAdapter(conn_str=settings.pg_dsn, auto_init=False)
    adapter.delete_by_source("doc_pt.md")
    adapter.delete_by_source("doc_en.md")
    initial_count = adapter.count()

    vec = [0.0] * 768
    c1 = DocumentChunk(
        content="Chunk 1",
        embedding=vec,
        source="doc_pt.md",
        metadata={"test_tag": "tag1"},
    )
    c2 = DocumentChunk(
        content="Chunk 2",
        embedding=vec,
        source="doc_en.md",
        metadata={"test_tag": "tag2"},
    )

    adapter.save_chunks([c1, c2])
    assert adapter.count() == initial_count + 2

    adapter.delete_by_source("doc_pt.md")
    assert adapter.count() == initial_count + 1

    adapter.delete_by_metadata("test_tag", "tag2")
    assert adapter.count() == initial_count
