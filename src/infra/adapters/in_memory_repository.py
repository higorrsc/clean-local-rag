from typing import Any

import numpy as np

from src.domain.entities import DocumentChunk
from src.domain.interfaces import AsyncVectorRepository, VectorRepository


class InMemoryVectorAdapter(VectorRepository, AsyncVectorRepository):
    """
    In-memory implementation of VectorRepository using NumPy for cosine similarity.
    Allows local testing and quick evaluation without external database dependencies.
    Implements both synchronous and asynchronous contracts.
    """

    def __init__(self) -> None:
        self._chunks: list[DocumentChunk] = []

    def save_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Persist document chunks into memory."""
        self._chunks.extend(chunks)

    async def asave_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Persist document chunks into memory asynchronously."""
        self.save_chunks(chunks)

    def search_similar(
        self,
        query_embedding: list[float],
        top_k: int = 4,
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Calculates cosine similarity between the query embedding and stored chunks,
        returning top_k tuples (DocumentChunk, score) sorted descending.
        """
        if not self._chunks:
            return []

        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)

        if q_norm == 0.0:
            return [(chunk, 0.0) for chunk in self._chunks[:top_k]]

        chunk_vecs = np.array(
            [chunk.embedding for chunk in self._chunks],
            dtype=np.float32,
        )
        chunk_norms = np.linalg.norm(chunk_vecs, axis=1)

        # Avoid division by zero
        chunk_norms = np.where(chunk_norms == 0.0, 1e-10, chunk_norms)

        # Dot product divided by (q_norm * chunk_norms)
        similarities = np.dot(chunk_vecs, q_vec) / (q_norm * chunk_norms)

        # Get indices of top_k sorted descending
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = [(self._chunks[idx], float(similarities[idx])) for idx in top_indices]
        return results

    async def asearch_similar(
        self,
        query_embedding: list[float],
        top_k: int = 4,
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Calculates cosine similarity asynchronously,
        returning top_k tuples sorted descending.
        """
        return self.search_similar(query_embedding=query_embedding, top_k=top_k)

    def clear(self) -> None:
        """Clear all stored chunks."""
        self._chunks.clear()

    async def aclear(self) -> None:
        """Clear all stored chunks asynchronously."""
        self.clear()

    def count(self) -> int:
        """Return number of stored chunks."""
        return len(self._chunks)

    async def acount(self) -> int:
        """Return number of stored chunks asynchronously."""
        return self.count()

    def delete_by_source(self, source: str) -> None:
        """Remove all chunks matching source identifier."""
        self._chunks = [c for c in self._chunks if c.source != source]

    async def adelete_by_source(self, source: str) -> None:
        """Remove all chunks matching source identifier asynchronously."""
        self.delete_by_source(source)

    def delete_by_metadata(self, key: str, value: Any) -> None:
        """Remove all chunks whose metadata contains key == value."""
        self._chunks = [c for c in self._chunks if c.metadata.get(key) != value]

    async def adelete_by_metadata(self, key: str, value: Any) -> None:
        """Remove all chunks matching metadata key/value asynchronously."""
        self.delete_by_metadata(key, value)
