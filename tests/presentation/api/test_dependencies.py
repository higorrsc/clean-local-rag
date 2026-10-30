from unittest.mock import patch

from src.infra.adapters.in_memory_repository import InMemoryVectorAdapter
from src.infra.adapters.pgvector_repository import PgVectorAdapter
from src.presentation.api import dependencies


def test_api_get_vector_repository_uses_factory():
    """Verify FastAPI dependencies use create_vector_repository."""
    with patch(
        "src.presentation.api.dependencies.create_vector_repository"
    ) as mock_factory:
        mock_repo = InMemoryVectorAdapter()
        mock_factory.return_value = mock_repo

        # Reset singleton cache
        dependencies._vector_repository = None
        repo = dependencies.get_vector_repository()

        mock_factory.assert_called_once()
        assert repo is mock_repo


def test_api_get_vector_repository_pgvector_backend():
    """Verify FastAPI dependencies instantiate PgVectorAdapter for pgvector."""
    with (
        patch("src.infra.adapters.pgvector_repository.psycopg.connect"),
        patch("src.config.settings.settings.vector_backend", "pgvector"),
    ):
        dependencies._vector_repository = None
        repo = dependencies.get_vector_repository()

        assert isinstance(repo, PgVectorAdapter)
