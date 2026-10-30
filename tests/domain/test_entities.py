from src.domain.entities import DocumentChunk, generate_chunk_id


def test_document_chunk_entity():
    chunk = DocumentChunk(content="test content", embedding=[0.1, 0.2])
    assert chunk.content == "test content"
    assert chunk.embedding == [0.1, 0.2]
    assert chunk.chunk_id is not None
    assert chunk.source is None


def test_generate_chunk_id_is_deterministic():
    id1 = generate_chunk_id("file.md", 0, "sample content")
    id2 = generate_chunk_id("file.md", 0, "sample content")
    id_different_idx = generate_chunk_id("file.md", 1, "sample content")
    id_different_src = generate_chunk_id("other.md", 0, "sample content")

    assert id1 == id2
    assert id1 != id_different_idx
    assert id1 != id_different_src
