from src.config.settings import Settings


def test_settings_defaults():
    s = Settings()
    assert s.vector_backend in ("memory", "pgvector")
    assert s.pg_dsn.startswith("postgresql://")
    assert s.embed_model == "nomic-embed-text:latest"
    assert s.chat_model == "qwen3:4b-instruct"
    assert s.ollama_timeout == 180.0


def test_settings_vector_backend_override():
    s = Settings(vector_backend="pgvector")
    assert s.vector_backend == "pgvector"

    s2 = Settings(vector_backend="memory")
    assert s2.vector_backend == "memory"
