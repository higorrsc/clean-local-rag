import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DocumentChunk:
    """
    Core domain entity representing a semantic slice of a document with its vector embedding.
    """

    content: str
    embedding: list[float]
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str | None = None
    source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
