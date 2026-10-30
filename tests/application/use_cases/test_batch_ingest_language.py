from pathlib import Path

import pytest

from src.application.use_cases.batch_ingest_language import (
    AsyncBatchIngestByLanguageUseCase,
)
from src.domain.models import BatchIngestRequest
from src.infra.adapters.in_memory_repository import InMemoryVectorAdapter


class FakeAsyncEmbedder:
    async def agenerate_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [[0.1 * i, 0.2, 0.3] for i in range(len(texts))]


@pytest.mark.anyio
async def test_batch_ingest_by_language_success(tmp_path: Path):
    lang_dir = tmp_path / "pt-br"
    lang_dir.mkdir(parents=True)
    doc1 = lang_dir / "doc1.md"
    doc1.write_text("# Barbearia 1\n\nInformações gerais.", encoding="utf-8")
    doc2 = lang_dir / "doc2.md"
    doc2.write_text("# Preços\n\nCorte custa R$ 50.", encoding="utf-8")

    repo = InMemoryVectorAdapter()
    embedder = FakeAsyncEmbedder()

    use_case = AsyncBatchIngestByLanguageUseCase(
        embedding_gateway=embedder,
        vector_repository=repo,
        docs_dir=tmp_path,
    )

    req = BatchIngestRequest(language="pt-br")
    res = await use_case.execute(req)

    assert res.status == "success"
    assert res.language == "pt-br"
    assert res.files_count == 2
    assert res.chunks_count == 2
    assert sorted(res.documents) == ["doc1.md", "doc2.md"]
    assert repo.count() == 2


@pytest.mark.anyio
async def test_batch_ingest_missing_directory(tmp_path: Path):
    repo = InMemoryVectorAdapter()
    embedder = FakeAsyncEmbedder()

    use_case = AsyncBatchIngestByLanguageUseCase(
        embedding_gateway=embedder,
        vector_repository=repo,
        docs_dir=tmp_path,
    )

    req = BatchIngestRequest(language="es")
    with pytest.raises(FileNotFoundError, match="not found"):
        await use_case.execute(req)


@pytest.mark.anyio
async def test_batch_ingest_empty_directory(tmp_path: Path):
    lang_dir = tmp_path / "fr"
    lang_dir.mkdir(parents=True)

    repo = InMemoryVectorAdapter()
    embedder = FakeAsyncEmbedder()

    use_case = AsyncBatchIngestByLanguageUseCase(
        embedding_gateway=embedder,
        vector_repository=repo,
        docs_dir=tmp_path,
    )

    req = BatchIngestRequest(language="fr")
    with pytest.raises(ValueError, match="No markdown"):
        await use_case.execute(req)
