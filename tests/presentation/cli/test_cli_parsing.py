import pytest

from src.presentation.cli.main import parse_interactive_ingest


def test_parse_interactive_ingest_direct_text():
    content, source = parse_interactive_ingest("Este é um texto simples")
    assert content == "Este é um texto simples"
    assert source == "sessão_interativa"


def test_parse_interactive_ingest_text_flag_with_source():
    content, source = parse_interactive_ingest(
        '-t "Texto entre aspas" -s custom_source'
    )
    assert content == "Texto entre aspas"
    assert source == "custom_source"


def test_parse_interactive_ingest_file_path(tmp_path):
    test_file = tmp_path / "sample.md"
    test_file.write_text("Conteúdo do arquivo de teste", encoding="utf-8")

    # Positional existing file path
    content, source = parse_interactive_ingest(str(test_file))
    assert content == "Conteúdo do arquivo de teste"
    assert source == "sample.md"

    # With -f flag
    content, source = parse_interactive_ingest(f"-f {test_file} -s doc_custom")
    assert content == "Conteúdo do arquivo de teste"
    assert source == "doc_custom"


def test_parse_interactive_ingest_empty_raises():
    with pytest.raises(ValueError, match="Forneça um caminho"):
        parse_interactive_ingest("   ")
