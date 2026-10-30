from src.domain.models import (
    BatchIngestRequest,
    BatchIngestResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    SourceChunk,
)


def test_health_response_model():
    res = HealthResponse(status="ok", version="0.1.0")
    assert res.status == "ok"
    assert res.version == "0.1.0"


def test_batch_ingest_models():
    req = BatchIngestRequest(language="pt-br")
    assert req.language == "pt-br"

    res = BatchIngestResponse(
        files_count=3,
        chunks_count=18,
        status="success",
        language="pt-br",
        documents=["visao-geral-e-unidades.md", "servicos-e-precos.md"],
    )
    assert res.files_count == 3
    assert res.chunks_count == 18
    assert res.status == "success"
    assert res.language == "pt-br"
    assert len(res.documents) == 2


def test_ingest_request_model():
    req = IngestRequest(
        content="Sample content", source="doc.txt", metadata={"tag": "v1"}
    )
    assert req.content == "Sample content"
    assert req.source == "doc.txt"
    assert req.metadata == {"tag": "v1"}


def test_ingest_response_model():
    res = IngestResponse(chunks_count=3, status="success", document_id="123")
    assert res.chunks_count == 3
    assert res.status == "success"
    assert res.document_id == "123"


def test_query_models():
    req = QueryRequest(question="Where is the branch?", top_k=2)
    assert req.question == "Where is the branch?"
    assert req.top_k == 2

    source = SourceChunk(content="chunk text", source="doc.txt", score=0.95)
    res = QueryResponse(answer="It is here.", sources=[source])
    assert res.answer == "It is here."
    assert len(res.sources) == 1
    assert res.sources[0].score == 0.95
