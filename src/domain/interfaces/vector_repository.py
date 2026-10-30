from typing import Protocol, runtime_checkable

from src.domain.entities.document_chunk import DocumentChunk


@runtime_checkable
class VectorRepository(Protocol):
    """Contract for vector persistence and similarity retrieval."""

    def save_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Persist document chunks and their embeddings."""

    def search_similar(
        self,
        query_embedding: list[float],
        top_k: int = 3,
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Search for top-k similar chunks given a query embedding.
        Returns a list of tuples (chunk, similarity_score) ordered by descending similarity.
        """
