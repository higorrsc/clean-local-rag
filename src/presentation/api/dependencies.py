from typing import Annotated

from fastapi import Depends

from src.application.use_cases import (
    AskQuestionUseCase,
    AsyncBatchIngestByLanguageUseCase,
    IngestDocumentsUseCase,
)
from src.domain.interfaces import (
    AsyncEmbeddingGateway,
    AsyncLLMGateway,
    AsyncVectorRepository,
)
from src.infra.adapters.ollama import OllamaAdapter
from src.infra.adapters.vector_factory import create_vector_repository

# Shared vector repository instance for context across requests
_vector_repository: AsyncVectorRepository | None = None
_ollama_adapter: OllamaAdapter | None = None


def get_vector_repository() -> AsyncVectorRepository:
    """Return the shared vector repository instance."""
    global _vector_repository
    if _vector_repository is None:
        _vector_repository = create_vector_repository()
    return _vector_repository


def get_ollama_adapter() -> OllamaAdapter:
    """Return the shared Ollama adapter instance."""
    global _ollama_adapter
    if _ollama_adapter is None:
        _ollama_adapter = OllamaAdapter()
    return _ollama_adapter


def get_batch_ingest_use_case(
    embedder: Annotated[AsyncEmbeddingGateway, Depends(get_ollama_adapter)],
    repo: Annotated[AsyncVectorRepository, Depends(get_vector_repository)],
) -> AsyncBatchIngestByLanguageUseCase:
    """Provide AsyncBatchIngestByLanguageUseCase with injected dependencies."""
    return AsyncBatchIngestByLanguageUseCase(
        embedding_gateway=embedder,
        vector_repository=repo,
    )


def get_ingest_use_case(
    embedder: Annotated[AsyncEmbeddingGateway, Depends(get_ollama_adapter)],
    repo: Annotated[AsyncVectorRepository, Depends(get_vector_repository)],
) -> IngestDocumentsUseCase:
    """Provide IngestDocumentsUseCase with injected dependencies."""
    return IngestDocumentsUseCase(
        embedding_gateway=embedder,
        vector_repository=repo,
    )


def get_ask_question_use_case(
    embedder: Annotated[AsyncEmbeddingGateway, Depends(get_ollama_adapter)],
    repo: Annotated[AsyncVectorRepository, Depends(get_vector_repository)],
    llm: Annotated[AsyncLLMGateway, Depends(get_ollama_adapter)],
) -> AskQuestionUseCase:
    """Provide AskQuestionUseCase with injected dependencies."""
    return AskQuestionUseCase(
        embedding_gateway=embedder,
        vector_repository=repo,
        llm_gateway=llm,
    )


# Dependency Type Aliases following FastAPI best practices
VectorRepoDep = Annotated[AsyncVectorRepository, Depends(get_vector_repository)]
OllamaAdapterDep = Annotated[OllamaAdapter, Depends(get_ollama_adapter)]
BatchIngestUseCaseDep = Annotated[
    AsyncBatchIngestByLanguageUseCase, Depends(get_batch_ingest_use_case)
]
IngestUseCaseDep = Annotated[IngestDocumentsUseCase, Depends(get_ingest_use_case)]
AskQuestionUseCaseDep = Annotated[
    AskQuestionUseCase, Depends(get_ask_question_use_case)
]
