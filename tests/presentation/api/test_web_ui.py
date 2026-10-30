from fastapi.testclient import TestClient

from src.presentation.api.main import app

client = TestClient(app)


def test_serve_interactive_web_ui():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Local RAG - Interactive Web UI" in response.text
    assert "Carregar Documentos" in response.text
    assert "Qual unidade é exclusiva para mulheres" in response.text
