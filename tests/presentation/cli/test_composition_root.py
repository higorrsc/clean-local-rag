from unittest.mock import patch

from src.infra.adapters.in_memory_repository import InMemoryVectorAdapter
from src.infra.adapters.pgvector_repository import PgVectorAdapter
from src.presentation.cli.main import get_adapters


def test_cli_get_adapters_uses_vector_factory():
    """Verify CLI composition root creates the repository via factory."""
    with patch("src.presentation.cli.main.create_vector_repository") as mock_factory:
        mock_repo = InMemoryVectorAdapter()
        mock_factory.return_value = mock_repo

        _embedder, repo, ingest_uc, ask_uc = get_adapters()

        mock_factory.assert_called_once()
        assert repo is mock_repo
        assert ingest_uc.vector_repository is mock_repo
        assert ask_uc.vector_repository is mock_repo


def test_cli_get_adapters_with_pgvector_backend():
    """Verify CLI composition root creates PgVectorAdapter when configured."""
    with (
        patch("src.infra.adapters.pgvector_repository.psycopg.connect"),
        patch("src.config.settings.settings.vector_backend", "pgvector"),
    ):
        _embedder, repo, ingest_uc, ask_uc = get_adapters()

        assert isinstance(repo, PgVectorAdapter)
        assert ingest_uc.vector_repository is repo
        assert ask_uc.vector_repository is repo
