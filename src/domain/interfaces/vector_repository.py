from typing import Any, Protocol, runtime_checkable

from src.domain.entities.document_chunk import DocumentChunk


@runtime_checkable
class VectorRepository(Protocol):
    """Contract for vector persistence and similarity retrieval."""

    def save_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Persist document chunks and their embeddings."""

    def search_similar(
        self,
        query_embedding: list[float],
        top_k: int = 4,
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Search for top-k similar chunks given a query embedding.
        Returns tuples of (chunk, similarity_score) sorted descending.
        """

    def delete_by_source(self, source: str) -> None:
        """Delete all chunks associated with the specified source identifier."""

    def delete_by_metadata(self, key: str, value: Any) -> None:
        """Delete all chunks whose metadata contains key == value."""


@runtime_checkable
class AsyncVectorRepository(Protocol):
    """Contract for asynchronous vector persistence and similarity retrieval."""

    async def asave_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Persist document chunks and their embeddings asynchronously."""

    async def asearch_similar(
        self,
        query_embedding: list[float],
        top_k: int = 4,
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Search for top-k similar chunks given a query embedding asynchronously.
        Returns tuples of (chunk, similarity_score) sorted descending.
        """

    async def adelete_by_source(self, source: str) -> None:
        """Delete all chunks associated with the source identifier asynchronously."""

    async def adelete_by_metadata(self, key: str, value: Any) -> None:
        """Delete all chunks whose metadata contains key == value asynchronously."""
