from src.config.settings import settings
from src.domain.interfaces import AsyncVectorRepository, VectorRepository
from src.infra.adapters.in_memory_repository import InMemoryVectorAdapter
from src.infra.adapters.pgvector_repository import PgVectorAdapter


def create_vector_repository(
    backend: str | None = None,
    conn_str: str | None = None,
) -> VectorRepository | AsyncVectorRepository:
    """
    Factory creating a VectorRepository instance based on configuration or parameter.
    Defaults to InMemoryVectorAdapter unless 'pgvector' is explicitly specified.
    """
    selected = (backend or settings.vector_backend).strip().lower()
    if selected == "pgvector":
        return PgVectorAdapter(conn_str=conn_str or settings.pg_dsn)
    return InMemoryVectorAdapter()
