import pytest

from src.application.use_cases.ask_question import AskQuestionUseCase
from src.domain.entities import DocumentChunk
from src.domain.models import QueryRequest


class FakeEmbeddingGateway:
    def generate_embedding(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


class FakeLLMGateway:
    def __init__(self, response: str = "Test response") -> None:
        self.response = response
        self.last_prompt: str | None = None
        self.last_system_prompt: str | None = None

    def generate_response(self, prompt: str, system_prompt: str | None = None) -> str:
        self.last_prompt = prompt
        self.last_system_prompt = system_prompt
        return self.response


class FakeVectorRepository:
    def __init__(self) -> None:
        self.chunks: list[DocumentChunk] = []

    def save_chunks(self, chunks: list[DocumentChunk]) -> None:
        self.chunks.extend(chunks)

    def search_similar(
        self, query_embedding: list[float], top_k: int = 3
    ) -> list[tuple[DocumentChunk, float]]:
        return [(c, 0.95) for c in self.chunks[:top_k]]


def test_ask_question_use_case_with_context():
    embedder = FakeEmbeddingGateway()
    repo = FakeVectorRepository()
    llm = FakeLLMGateway(response="Python was created by Guido van Rossum.")
    use_case = AskQuestionUseCase(embedder, repo, llm)

    chunk = DocumentChunk(
        content="Python is created by Guido.",
        embedding=[0.1, 0.2, 0.3],
        source="python.txt",
    )
    repo.save_chunks([chunk])

    request = QueryRequest(question="Who created Python?", top_k=1)
    response = use_case.execute(request)

    assert response.answer == "Python was created by Guido van Rossum."
    assert len(response.sources) == 1
    assert response.sources[0].source == "python.txt"
    assert llm.last_prompt is not None
    assert "Who created Python?" in llm.last_prompt


def test_ask_question_use_case_empty_repo():
    embedder = FakeEmbeddingGateway()
    repo = FakeVectorRepository()
    llm = FakeLLMGateway()
    use_case = AskQuestionUseCase(embedder, repo, llm)

    request = QueryRequest(question="Any question?", top_k=2)
    response = use_case.execute(request)

    assert len(response.sources) == 0
    assert "Não foram encontradas" in response.answer


def test_ask_question_empty_query_raises():
    embedder = FakeEmbeddingGateway()
    repo = FakeVectorRepository()
    llm = FakeLLMGateway()
    use_case = AskQuestionUseCase(embedder, repo, llm)

    with pytest.raises(ValueError, match="cannot be empty"):
        use_case.execute(QueryRequest(question="   "))
