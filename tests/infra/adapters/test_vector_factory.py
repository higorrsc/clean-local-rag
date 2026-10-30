from src.config.settings import Settings
from src.infra.adapters.in_memory_repository import InMemoryVectorAdapter
from src.infra.adapters.pgvector_repository import PgVectorAdapter
from src.infra.adapters.vector_factory import create_vector_repository


def test_create_vector_repository_default_memory(monkeypatch):
    test_settings = Settings(vector_backend="memory")
    monkeypatch.setattr("src.infra.adapters.vector_factory.settings", test_settings)

    repo = create_vector_repository()
    assert isinstance(repo, InMemoryVectorAdapter)


def test_create_vector_repository_explicit_pgvector():
    repo = create_vector_repository(backend="pgvector", conn_str="postgresql://test")
    assert isinstance(repo, PgVectorAdapter)
    assert repo.conn_str == "postgresql://test"


def test_create_vector_repository_explicit_memory():
    repo = create_vector_repository(backend="memory")
    assert isinstance(repo, InMemoryVectorAdapter)
