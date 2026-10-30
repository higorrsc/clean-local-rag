from src.domain.entities import DocumentChunk


def test_document_chunk_entity():
    chunk = DocumentChunk(content="test content", embedding=[0.1, 0.2])
    assert chunk.content == "test content"
    assert chunk.embedding == [0.1, 0.2]
    assert chunk.chunk_id is not None
    assert chunk.source is None
