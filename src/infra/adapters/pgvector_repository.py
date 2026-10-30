import json
from typing import Any

import psycopg
from pgvector.psycopg import register_vector, register_vector_async

from src.config.settings import settings
from src.domain.entities import DocumentChunk
from src.domain.interfaces import AsyncVectorRepository, VectorRepository

INIT_SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT,
    content TEXT NOT NULL,
    source TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(768) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
ON document_chunks USING hnsw (embedding vector_cosine_ops);
"""


class PgVectorAdapter(VectorRepository, AsyncVectorRepository):
    """
    PostgreSQL vector repository adapter using psycopg (v3) and pgvector.
    Executes raw SQL without ORMs, supporting both sync and async contracts.
    """

    def __init__(
        self,
        conn_str: str | None = None,
        auto_init: bool = True,
    ) -> None:
        self.conn_str = conn_str or settings.pg_dsn
        self.auto_init = auto_init
        self._initialized = False

    def init_db(self) -> None:
        """Initialize database schema, extension and table idempotently."""
        try:
            with psycopg.connect(self.conn_str, autocommit=True) as conn:
                with conn.cursor() as cur:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                register_vector(conn)
                with conn.cursor() as cur:
                    cur.execute(INIT_SCHEMA_SQL)
            self._initialized = True
        except Exception as e:
            msg = (
                f"Failed to initialize pgvector database at '{self.conn_str}'. "
                "Ensure PostgreSQL is running (e.g. `docker compose up -d postgres`)."
            )
            raise ConnectionError(msg) from e

    async def ainit_db(self) -> None:
        """Initialize database schema asynchronously."""
        try:
            async with await psycopg.AsyncConnection.connect(
                self.conn_str, autocommit=True
            ) as aconn:
                async with aconn.cursor() as cur:
                    await cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                await register_vector_async(aconn)
                async with aconn.cursor() as cur:
                    await cur.execute(INIT_SCHEMA_SQL)
            self._initialized = True
        except Exception as e:
            msg = (
                f"Failed to initialize pgvector database at '{self.conn_str}'. "
                "Ensure PostgreSQL is running (e.g. `docker compose up -d postgres`)."
            )
            raise ConnectionError(msg) from e

    def _ensure_initialized(self) -> None:
        if self.auto_init and not self._initialized:
            self.init_db()

    async def _aensure_initialized(self) -> None:
        if self.auto_init and not self._initialized:
            await self.ainit_db()

    def save_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Persist document chunks and their vector embeddings synchronously."""
        if not chunks:
            return
        self._ensure_initialized()

        insert_sql = """
        INSERT INTO document_chunks (
            chunk_id, document_id, content, source, metadata, embedding
        ) VALUES (
            %(chunk_id)s, %(document_id)s, %(content)s,
            %(source)s, %(metadata)s, %(embedding)s::vector
        )
        ON CONFLICT (chunk_id) DO UPDATE SET
            content = EXCLUDED.content,
            embedding = EXCLUDED.embedding,
            metadata = EXCLUDED.metadata;
        """

        with psycopg.connect(self.conn_str, autocommit=True) as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                for chunk in chunks:
                    params: dict[str, Any] = {
                        "chunk_id": chunk.chunk_id,
                        "document_id": chunk.document_id,
                        "content": chunk.content,
                        "source": chunk.source,
                        "metadata": json.dumps(chunk.metadata),
                        "embedding": chunk.embedding,
                    }
                    cur.execute(insert_sql, params)

    async def asave_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Persist document chunks and embeddings asynchronously."""
        if not chunks:
            return
        await self._aensure_initialized()

        insert_sql = """
        INSERT INTO document_chunks (
            chunk_id, document_id, content, source, metadata, embedding
        ) VALUES (
            %(chunk_id)s, %(document_id)s, %(content)s,
            %(source)s, %(metadata)s, %(embedding)s::vector
        )
        ON CONFLICT (chunk_id) DO UPDATE SET
            content = EXCLUDED.content,
            embedding = EXCLUDED.embedding,
            metadata = EXCLUDED.metadata;
        """

        async with await psycopg.AsyncConnection.connect(
            self.conn_str, autocommit=True
        ) as aconn:
            await register_vector_async(aconn)
            async with aconn.cursor() as cur:
                for chunk in chunks:
                    params: dict[str, Any] = {
                        "chunk_id": chunk.chunk_id,
                        "document_id": chunk.document_id,
                        "content": chunk.content,
                        "source": chunk.source,
                        "metadata": json.dumps(chunk.metadata),
                        "embedding": chunk.embedding,
                    }
                    await cur.execute(insert_sql, params)

    def search_similar(
        self,
        query_embedding: list[float],
        top_k: int = 4,
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Search for top-k nearest chunks using native cosine distance (<=>).
        Returns list of (DocumentChunk, score) sorted by descending similarity.
        """
        self._ensure_initialized()

        query_sql = """
        SELECT chunk_id, document_id, content, source, metadata,
               1 - (embedding <=> %(embedding)s::vector) AS score
        FROM document_chunks
        ORDER BY embedding <=> %(embedding)s::vector
        LIMIT %(top_k)s;
        """

        results: list[tuple[DocumentChunk, float]] = []
        with psycopg.connect(self.conn_str) as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                cur.execute(
                    query_sql,
                    {"embedding": query_embedding, "top_k": top_k},
                )
                rows = cur.fetchall()
                for row in rows:
                    meta = (
                        json.loads(row[4])
                        if isinstance(row[4], str)
                        else (row[4] or {})
                    )
                    chunk = DocumentChunk(
                        chunk_id=row[0],
                        document_id=row[1],
                        content=row[2],
                        source=row[3],
                        metadata=meta,
                        embedding=[],
                    )
                    results.append((chunk, float(row[5])))
        return results

    async def asearch_similar(
        self,
        query_embedding: list[float],
        top_k: int = 4,
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Search for top-k nearest chunks using native cosine distance asynchronously.
        """
        await self._aensure_initialized()

        query_sql = """
        SELECT chunk_id, document_id, content, source, metadata,
               1 - (embedding <=> %(embedding)s::vector) AS score
        FROM document_chunks
        ORDER BY embedding <=> %(embedding)s::vector
        LIMIT %(top_k)s;
        """

        results: list[tuple[DocumentChunk, float]] = []
        async with await psycopg.AsyncConnection.connect(self.conn_str) as aconn:
            await register_vector_async(aconn)
            async with aconn.cursor() as cur:
                await cur.execute(
                    query_sql,
                    {"embedding": query_embedding, "top_k": top_k},
                )
                rows = await cur.fetchall()
                for row in rows:
                    meta = (
                        json.loads(row[4])
                        if isinstance(row[4], str)
                        else (row[4] or {})
                    )
                    chunk = DocumentChunk(
                        chunk_id=row[0],
                        document_id=row[1],
                        content=row[2],
                        source=row[3],
                        metadata=meta,
                        embedding=[],
                    )
                    results.append((chunk, float(row[5])))
        return results

    def count(self) -> int:
        """Return total number of chunks stored in PostgreSQL."""
        self._ensure_initialized()
        with psycopg.connect(self.conn_str) as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM document_chunks;")
            row = cur.fetchone()
            return int(row[0]) if row else 0

    async def acount(self) -> int:
        """Return total number of chunks asynchronously."""
        await self._aensure_initialized()
        async with (
            await psycopg.AsyncConnection.connect(self.conn_str) as aconn,
            aconn.cursor() as cur,
        ):
            await cur.execute("SELECT COUNT(*) FROM document_chunks;")
            row = await cur.fetchone()
            return int(row[0]) if row else 0

    def clear(self) -> None:
        """Truncate all document chunks from table."""
        self._ensure_initialized()
        with (
            psycopg.connect(self.conn_str, autocommit=True) as conn,
            conn.cursor() as cur,
        ):
            cur.execute("TRUNCATE TABLE document_chunks;")

    async def aclear(self) -> None:
        """Truncate all document chunks asynchronously."""
        await self._aensure_initialized()
        async with (
            await psycopg.AsyncConnection.connect(
                self.conn_str, autocommit=True
            ) as aconn,
            aconn.cursor() as cur,
        ):
            await cur.execute("TRUNCATE TABLE document_chunks;")
