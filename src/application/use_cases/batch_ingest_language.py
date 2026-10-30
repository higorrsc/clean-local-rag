import uuid
from pathlib import Path

from src.application.use_cases.ingest_documents import chunk_text
from src.domain.entities import DocumentChunk, generate_chunk_id
from src.domain.interfaces import (
    AsyncEmbeddingGateway,
    AsyncVectorRepository,
    EmbeddingGateway,
    VectorRepository,
)
from src.domain.models import BatchIngestRequest, BatchIngestResponse


class AsyncBatchIngestByLanguageUseCase:
    """
    Asynchronously scans docs/<language> for markdown files,
    chunks them, computes embeddings, and persists them into repository.
    """

    def __init__(
        self,
        embedding_gateway: AsyncEmbeddingGateway | EmbeddingGateway,
        vector_repository: AsyncVectorRepository | VectorRepository,
        docs_dir: Path | str = "docs",
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
    ) -> None:
        self.embedding_gateway = embedding_gateway
        self.vector_repository = vector_repository
        self.docs_dir = Path(docs_dir)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def execute(self, request: BatchIngestRequest) -> BatchIngestResponse:
        language = (request.language or "").strip().lower()
        if not language:
            raise ValueError("Language parameter must not be empty.")

        target_dir = self.docs_dir / language
        if not target_dir.exists() or not target_dir.is_dir():
            raise FileNotFoundError(
                f"Directory for language '{language}' was not found at '{target_dir}'."
            )

        md_files = sorted(target_dir.glob("*.md"))
        if not md_files:
            raise ValueError(
                f"No markdown (.md) documents found in directory '{target_dir}'."
            )

        total_chunks: list[DocumentChunk] = []
        ingested_documents: list[str] = []

        for md_file in md_files:
            content = md_file.read_text(encoding="utf-8").strip()
            if not content:
                continue

            text_chunks = chunk_text(
                content,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )
            if not text_chunks:
                continue

            # Compute embeddings asynchronously if available
            if hasattr(self.embedding_gateway, "agenerate_embeddings"):
                embeddings = await self.embedding_gateway.agenerate_embeddings(
                    text_chunks
                )
            else:
                embeddings = self.embedding_gateway.generate_embeddings(text_chunks)

            if len(embeddings) != len(text_chunks):
                raise RuntimeError(
                    f"Mismatch in embeddings for file {md_file.name}: "
                    f"expected {len(text_chunks)}, got {len(embeddings)}."
                )

            doc_id = str(uuid.uuid4())
            for idx, (text, emb) in enumerate(
                zip(text_chunks, embeddings, strict=True)
            ):
                chunk_id = generate_chunk_id(md_file.name, idx, text)
                total_chunks.append(
                    DocumentChunk(
                        content=text,
                        embedding=emb,
                        chunk_id=chunk_id,
                        document_id=doc_id,
                        source=md_file.name,
                        metadata={
                            "language": language,
                            "filename": md_file.name,
                        },
                    )
                )

            ingested_documents.append(md_file.name)

        if not total_chunks:
            raise ValueError(
                f"No valid chunks extracted from markdown files in '{target_dir}'."
            )

        # Remove previous chunks for the language to ensure idempotency
        if hasattr(self.vector_repository, "adelete_by_metadata"):
            await self.vector_repository.adelete_by_metadata("language", language)
        elif hasattr(self.vector_repository, "delete_by_metadata"):
            self.vector_repository.delete_by_metadata("language", language)
        else:
            for doc_name in ingested_documents:
                if hasattr(self.vector_repository, "adelete_by_source"):
                    await self.vector_repository.adelete_by_source(doc_name)
                elif hasattr(self.vector_repository, "delete_by_source"):
                    self.vector_repository.delete_by_source(doc_name)

        # Persist chunks asynchronously if available
        if hasattr(self.vector_repository, "asave_chunks"):
            await self.vector_repository.asave_chunks(total_chunks)
        else:
            self.vector_repository.save_chunks(total_chunks)

        return BatchIngestResponse(
            files_count=len(ingested_documents),
            chunks_count=len(total_chunks),
            status="success",
            language=language,
            documents=ingested_documents,
        )
