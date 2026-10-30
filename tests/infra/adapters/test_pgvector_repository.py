import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities import DocumentChunk
from src.domain.interfaces import AsyncVectorRepository, VectorRepository
from src.infra.adapters.pgvector_repository import PgVectorAdapter


def test_pgvector_adapter_implements_protocols():
    adapter = PgVectorAdapter(auto_init=False)
    assert isinstance(adapter, VectorRepository)
    assert isinstance(adapter, AsyncVectorRepository)


@patch("src.infra.adapters.pgvector_repository.psycopg.connect")
@patch("src.infra.adapters.pgvector_repository.register_vector")
def test_pgvector_init_db(mock_register, mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connect.return_value.__enter__.return_value = mock_conn

    adapter = PgVectorAdapter(auto_init=False)
    adapter.init_db()

    mock_connect.assert_called_once_with(adapter.conn_str, autocommit=True)
    mock_register.assert_called_once_with(mock_conn)
    assert mock_cursor.execute.call_count == 2
    assert (
        "CREATE EXTENSION IF NOT EXISTS vector"
        in mock_cursor.execute.call_args_list[0][0][0]
    )


@patch("src.infra.adapters.pgvector_repository.psycopg.connect")
def test_pgvector_init_db_connection_error(mock_connect):
    mock_connect.side_effect = Exception("DB unreachable")

    adapter = PgVectorAdapter(auto_init=False)
    with pytest.raises(ConnectionError) as exc_info:
        adapter.init_db()

    assert "Failed to initialize pgvector database" in str(exc_info.value)
    assert "docker compose up -d postgres" in str(exc_info.value)


@patch("src.infra.adapters.pgvector_repository.psycopg.connect")
@patch("src.infra.adapters.pgvector_repository.register_vector")
def test_pgvector_save_chunks(mock_register, mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connect.return_value.__enter__.return_value = mock_conn

    adapter = PgVectorAdapter(auto_init=False)
    adapter._initialized = True

    chunk = DocumentChunk(
        content="Test content",
        embedding=[0.1, 0.2, 0.3],
        document_id="doc-123",
        source="file.txt",
        metadata={"lang": "en"},
    )
    adapter.save_chunks([chunk])

    mock_cursor.execute.assert_called_once()
    query, params = mock_cursor.execute.call_args[0]
    assert "INSERT INTO document_chunks" in query
    assert params["content"] == "Test content"
    assert params["source"] == "file.txt"
    assert params["metadata"] == json.dumps({"lang": "en"})
    assert params["embedding"] == [0.1, 0.2, 0.3]


@patch("src.infra.adapters.pgvector_repository.psycopg.connect")
@patch("src.infra.adapters.pgvector_repository.register_vector")
def test_pgvector_search_similar(mock_register, mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connect.return_value.__enter__.return_value = mock_conn

    mock_cursor.fetchall.return_value = [
        (
            "chunk-1",
            "doc-1",
            "Matched text",
            "doc.md",
            json.dumps({"tag": "v1"}),
            0.92,
        )
    ]

    adapter = PgVectorAdapter(auto_init=False)
    adapter._initialized = True

    results = adapter.search_similar(query_embedding=[0.1, 0.2], top_k=2)

    assert len(results) == 1
    chunk, score = results[0]
    assert chunk.content == "Matched text"
    assert chunk.source == "doc.md"
    assert chunk.metadata == {"tag": "v1"}
    assert score == 0.92


@patch("src.infra.adapters.pgvector_repository.psycopg.connect")
def test_pgvector_count_and_clear(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connect.return_value.__enter__.return_value = mock_conn

    mock_cursor.fetchone.return_value = [10]

    adapter = PgVectorAdapter(auto_init=False)
    adapter._initialized = True

    total = adapter.count()
    assert total == 10

    adapter.clear()
    assert "TRUNCATE TABLE" in mock_cursor.execute.call_args[0][0]


@patch("src.infra.adapters.pgvector_repository.psycopg.connect")
def test_pgvector_delete_by_source_and_metadata(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connect.return_value.__enter__.return_value = mock_conn

    adapter = PgVectorAdapter(auto_init=False)
    adapter._initialized = True

    adapter.delete_by_source("test.md")
    assert (
        "DELETE FROM document_chunks WHERE source ="
        in (mock_cursor.execute.call_args[0][0])
    )

    adapter.delete_by_metadata("lang", "pt-br")
    assert (
        "DELETE FROM document_chunks WHERE metadata->>"
        in (mock_cursor.execute.call_args[0][0])
    )


@pytest.mark.anyio
@patch(
    "src.infra.adapters.pgvector_repository.psycopg.AsyncConnection.connect",
    new_callable=AsyncMock,
)
@patch(
    "src.infra.adapters.pgvector_repository.register_vector_async",
    new_callable=AsyncMock,
)
async def test_pgvector_async_operations(mock_register_async, mock_aconnect):
    mock_aconn = MagicMock()
    mock_acursor = AsyncMock()
    mock_aconn.__aenter__.return_value = mock_aconn
    mock_aconn.__aexit__.return_value = None
    mock_aconn.cursor.return_value.__aenter__.return_value = mock_acursor
    mock_aconn.cursor.return_value.__aexit__.return_value = None
    mock_aconnect.return_value = mock_aconn

    adapter = PgVectorAdapter(auto_init=False)
    adapter._initialized = True

    chunk = DocumentChunk(
        content="Async text",
        embedding=[0.5, 0.5],
        source="async.md",
    )
    await adapter.asave_chunks([chunk])
    assert mock_acursor.execute.call_count == 1

    mock_acursor.fetchall.return_value = [
        ("chunk-async", "doc-1", "Async text", "async.md", "{}", 0.95)
    ]
    results = await adapter.asearch_similar(query_embedding=[0.5, 0.5], top_k=1)
    assert len(results) == 1
    assert results[0][0].content == "Async text"
    assert results[0][1] == 0.95

    mock_acursor.fetchone.return_value = [5]
    total = await adapter.acount()
    assert total == 5

    await adapter.aclear()
    assert "TRUNCATE TABLE" in mock_acursor.execute.call_args[0][0]
