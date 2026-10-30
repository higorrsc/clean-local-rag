import json

import httpx
from typer.testing import CliRunner

from src.application.use_cases import AskQuestionUseCase, IngestDocumentsUseCase
from src.domain.models import IngestRequest, QueryRequest
from src.infra.adapters.in_memory_repository import InMemoryVectorAdapter
from src.infra.adapters.ollama import OllamaAdapter
from src.presentation.cli.main import app, in_memory_repo

runner = CliRunner()


def test_end_to_end_in_memory_rag_pipeline():
    """
    Validates full end-to-end cycle: Ingest documents -> Generate embeddings ->
    Store in-memory -> Query -> Retrieve context -> Generate LLM answer.
    """

    def mock_ollama_handler(request: httpx.Request) -> httpx.Response:
        url_path = request.url.path
        body = json.loads(request.read().decode("utf-8"))

        if url_path == "/api/embed":
            inputs = body.get("input", [])
            if isinstance(inputs, str):
                inputs = [inputs]

            embeddings = []
            for item in inputs:
                if "Clean Architecture" in item:
                    embeddings.append([0.95, 0.05, 0.0])
                else:
                    embeddings.append([0.1, 0.1, 0.1])
            return httpx.Response(200, json={"embeddings": embeddings})

        elif url_path == "/api/chat":
            return httpx.Response(
                200,
                json={
                    "message": {
                        "content": (
                            "Clean Architecture organiza o software "
                            "em camadas concêntricas."
                        )
                    }
                },
            )

        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(mock_ollama_handler))
    embedder_llm = OllamaAdapter(client=client)
    repo = InMemoryVectorAdapter()

    ingest_use_case = IngestDocumentsUseCase(
        embedding_gateway=embedder_llm,
        vector_repository=repo,
        chunk_size=100,
        chunk_overlap=20,
    )
    ask_use_case = AskQuestionUseCase(
        embedding_gateway=embedder_llm,
        vector_repository=repo,
        llm_gateway=embedder_llm,
    )

    # 1. Ingest
    ingest_res = ingest_use_case.execute(
        IngestRequest(
            content=(
                "Documento sobre Clean Architecture. "
                "Separação de conceitos em camadas independentes."
            ),
            source="clean_arch.txt",
        )
    )

    assert ingest_res.status == "success"
    assert ingest_res.chunks_count >= 1
    assert repo.count() == ingest_res.chunks_count

    # 2. Ask
    query_res = ask_use_case.execute(
        QueryRequest(question="O que é Clean Architecture?", top_k=2)
    )

    assert "Clean Architecture" in query_res.answer
    assert len(query_res.sources) >= 1
    assert query_res.sources[0].source == "clean_arch.txt"
    assert query_res.sources[0].score > 0.8


def test_cli_ingest_and_ask_commands(monkeypatch):
    """
    Validates CLI command execution using Typer CliRunner and mocked Ollama client.
    """
    in_memory_repo.clear()

    def mock_handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        body = json.loads(request.read().decode("utf-8"))

        if path == "/api/embed":
            inputs = body.get("input", [])
            if isinstance(inputs, str):
                inputs = [inputs]
            embeddings = [[0.5, 0.5, 0.0] for _ in inputs]
            return httpx.Response(200, json={"embeddings": embeddings})
        elif path == "/api/chat":
            return httpx.Response(
                200, json={"message": {"content": "Resposta via CLI simulada."}}
            )
        return httpx.Response(404)

    mock_client = httpx.Client(transport=httpx.MockTransport(mock_handler))

    # Monkeypatch get_adapters in presentation.cli.main
    import src.presentation.cli.main as cli_main

    def patched_get_adapters():
        adapter = OllamaAdapter(client=mock_client)
        ingest_uc = IngestDocumentsUseCase(adapter, in_memory_repo)
        ask_uc = AskQuestionUseCase(adapter, in_memory_repo, adapter)
        return adapter, in_memory_repo, ingest_uc, ask_uc

    monkeypatch.setattr(cli_main, "get_adapters", patched_get_adapters)

    # Test ingest command
    result_ingest = runner.invoke(
        app,
        ["ingest", "--text", "Conteúdo de teste via CLI", "--source", "cli_test"],
    )
    assert result_ingest.exit_code == 0
    assert "Sucesso na Ingestão!" in result_ingest.stdout
    assert in_memory_repo.count() >= 1

    # Test ask command
    result_ask = runner.invoke(app, ["ask", "Qual o conteúdo?", "--top-k", "1"])
    assert result_ask.exit_code == 0
    assert "Resposta do Assistente" in result_ask.stdout
    assert "Resposta via CLI simulada." in result_ask.stdout
