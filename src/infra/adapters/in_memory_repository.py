import numpy as np

from src.domain.entities import DocumentChunk
from src.domain.interfaces import VectorRepository


class InMemoryVectorAdapter(VectorRepository):
    """
    In-memory implementation of VectorRepository using NumPy for cosine similarity.
    Allows local testing and quick evaluation without external database dependencies.
    """

    def __init__(self) -> None:
        self._chunks: list[DocumentChunk] = []

    def save_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Persist document chunks into memory."""
        self._chunks.extend(chunks)

    def search_similar(
        self,
        query_embedding: list[float],
        top_k: int = 3,
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

    def clear(self) -> None:
        """Clear all stored chunks."""
        self._chunks.clear()

    def count(self) -> int:
        """Return number of stored chunks."""
        return len(self._chunks)
