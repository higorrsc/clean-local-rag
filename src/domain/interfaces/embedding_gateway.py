from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingGateway(Protocol):
    """Contract for vector embedding services."""

    def generate_embedding(self, text: str) -> list[float]:
        """Generate vector embedding for a single text."""

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for a list of texts."""
