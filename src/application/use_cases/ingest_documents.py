import uuid

from src.domain.entities import DocumentChunk
from src.domain.interfaces import EmbeddingGateway, VectorRepository
from src.domain.models import IngestRequest, IngestResponse


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
) -> list[str]:
    """
    Splits text into chunks of roughly `chunk_size` characters with `chunk_overlap`.
    Prioritizes paragraph breaks (\n\n) and line breaks (\n) to keep markdown sections intact.
    """
    clean_text = text.strip()
    if not clean_text:
        return []

    if len(clean_text) <= chunk_size:
        return [clean_text]

    chunks: list[str] = []
    start = 0
    text_length = len(clean_text)

    while start < text_length:
        end = start + chunk_size
        if end >= text_length:
            chunks.append(clean_text[start:].strip())
            break

        # 1. Prioritize splitting at paragraph break \n\n
        split_pos = clean_text.rfind("\n\n", start, end)
        if split_pos != -1 and split_pos > start + (chunk_size // 3):
            chunk = clean_text[start:split_pos].strip()
            if chunk:
                chunks.append(chunk)
            start = split_pos + 2
            continue

        # 2. Prioritize splitting at newline \n
        split_pos = clean_text.rfind("\n", start, end)
        if split_pos != -1 and split_pos > start + (chunk_size // 3):
            chunk = clean_text[start:split_pos].strip()
            if chunk:
                chunks.append(chunk)
            start = split_pos + 1
            continue

        # 3. Fallback to space / word boundary
        split_pos = clean_text.rfind(" ", start, end)
        if split_pos == -1 or split_pos <= start:
            split_pos = end

        chunk = clean_text[start:split_pos].strip()
        if chunk:
            chunks.append(chunk)

        # Advance start with overlap
        start = max(split_pos - chunk_overlap, start + 1)

    return chunks


class IngestDocumentsUseCase:
    """
    Orchestrates document ingestion: chunking, vectorization, and persistence.
    """

    def __init__(
        self,
        embedding_gateway: EmbeddingGateway,
        vector_repository: VectorRepository,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
    ) -> None:
        self.embedding_gateway = embedding_gateway
        self.vector_repository = vector_repository
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def execute(self, request: IngestRequest) -> IngestResponse:
        content = (request.content or "").strip()
        if not content:
            raise ValueError("Document content cannot be empty.")

        text_chunks = chunk_text(
            content,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

        if not text_chunks:
            raise ValueError("No valid chunks could be extracted from document.")

        # Vectorize chunks
        embeddings = self.embedding_gateway.generate_embeddings(text_chunks)
        if len(embeddings) != len(text_chunks):
            raise RuntimeError(
                f"Mismatch: expected {len(text_chunks)} embeddings, got {len(embeddings)}."
            )

        doc_id = str(uuid.uuid4())
        chunks: list[DocumentChunk] = []

        for text, embedding in zip(text_chunks, embeddings, strict=True):
            chunks.append(
                DocumentChunk(
                    content=text,
                    embedding=embedding,
                    document_id=doc_id,
                    source=request.source,
                    metadata=request.metadata or {},
                )
            )

        # Persist chunks in repository
        self.vector_repository.save_chunks(chunks)

        return IngestResponse(
            chunks_count=len(chunks),
            status="success",
            document_id=doc_id,
        )
