import hashlib
import uuid
from dataclasses import dataclass, field
from typing import Any


def generate_chunk_id(source: str | None, index: int, content: str) -> str:
    """
    Generate a deterministic UUIDv5 chunk ID based on source, index,
    and content hash. Ensures identical text chunks from the same source
    receive identical IDs across re-ingestion runs.
    """
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
    key = f"{source or 'direct'}:{index}:{content_hash}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, key))


@dataclass(frozen=True)
class DocumentChunk:
    """
    Core domain entity representing a semantic slice of a document
    with its vector embedding.
    """

    content: str
    embedding: list[float]
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str | None = None
    source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
