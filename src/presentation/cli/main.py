import shlex
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.application.use_cases import AskQuestionUseCase, IngestDocumentsUseCase
from src.config.settings import settings
from src.domain.interfaces import VectorRepository
from src.domain.models import IngestRequest, QueryRequest
from src.infra.adapters.in_memory_repository import InMemoryVectorAdapter
from src.infra.adapters.ollama import OllamaAdapter
from src.infra.adapters.vector_factory import create_vector_repository

app = typer.Typer(
    name="rag-cli",
    help="Local RAG CLI application powered by Ollama and vector search.",
    add_completion=False,
)
console = Console()

# Singleton in-memory repository instance for CLI in-memory sessions/tests
in_memory_repo: VectorRepository = InMemoryVectorAdapter()


def get_backend_name(repo: VectorRepository | None = None) -> str:
    """Return the display name of the active vector backend."""
    if repo is not None and type(repo).__name__ == "InMemoryVectorAdapter":
        return "MEMORY"
    if repo is not None and type(repo).__name__ == "PgVectorAdapter":
        return "PGVECTOR"
    return settings.vector_backend.upper()


def get_adapters(
    repo: VectorRepository | None = None,
    backend: str | None = None,
) -> tuple[
    OllamaAdapter,
    VectorRepository,
    IngestDocumentsUseCase,
    AskQuestionUseCase,
]:
    """Composition Root: wires adapters and use cases."""
    embedder_llm = OllamaAdapter()
    active_repo = (
        repo if repo is not None else create_vector_repository(backend=backend)
    )
    ingest_use_case = IngestDocumentsUseCase(
        embedding_gateway=embedder_llm,
        vector_repository=active_repo,
    )
    ask_use_case = AskQuestionUseCase(
        embedding_gateway=embedder_llm,
        vector_repository=active_repo,
        llm_gateway=embedder_llm,
    )
    return embedder_llm, active_repo, ingest_use_case, ask_use_case


@app.command()
def ingest(
    text: Annotated[
        str | None,
        typer.Option(
            "--text",
            "-t",
            help="Raw text content to ingest into the RAG base.",
        ),
    ] = None,
    file: Annotated[
        Path | None,
        typer.Option(
            "--file",
            "-f",
            help="Path to a text file to read and ingest.",
            exists=True,
            dir_okay=False,
        ),
    ] = None,
    source: Annotated[
        str | None,
        typer.Option(
            "--source",
            "-s",
            help="Source identifier (e.g. filename or label).",
        ),
    ] = None,
    backend: Annotated[
        str | None,
        typer.Option(
            "--backend",
            "-b",
            help="Vector storage backend ('memory' or 'pgvector').",
        ),
    ] = None,
) -> None:
    """
    Ingest a document (from text or file) into the vector repository.
    """
    if not text and not file:
        console.print(
            "[bold red]Erro:[/bold red] Forneça um texto via `--text` "
            "ou um arquivo via `--file`.",
        )
        raise typer.Exit(code=1)

    content = text
    src_label = source

    if file:
        try:
            content = file.read_text(encoding="utf-8")
            if not src_label:
                src_label = file.name
        except Exception as e:
            console.print(f"[bold red]Erro ao ler o arquivo {file}:[/bold red] {e}")
            raise typer.Exit(code=1) from e

    if backend:
        _, repo, ingest_uc, _ = get_adapters(backend=backend)
    else:
        _, repo, ingest_uc, _ = get_adapters()
    backend_name = get_backend_name(repo)

    try:
        req = IngestRequest(content=content or "", source=src_label)
        res = ingest_uc.execute(req)
        console.print(
            Panel(
                f"[bold green]Sucesso na Ingestão![/bold green]\n\n"
                f"• Backend: [bold magenta]{backend_name}[/bold magenta]\n"
                f"• Chunks indexados: [cyan]{res.chunks_count}[/cyan]\n"
                f"• Origem: [yellow]{src_label or 'texto direto'}[/yellow]\n"
                f"• ID do Documento: [dim]{res.document_id}[/dim]",
                title="RAG Ingest",
            )
        )
    except Exception as e:
        console.print(f"[bold red]Falha durante a ingestão:[/bold red] {e}")
        raise typer.Exit(code=1) from e


@app.command()
def ask(
    question: Annotated[str, typer.Argument(help="Pergunta para o assistente RAG.")],
    top_k: Annotated[
        int,
        typer.Option(
            "--top-k",
            "-k",
            help="Número de chunks mais relevantes a recuperar.",
        ),
    ] = 4,
    backend: Annotated[
        str | None,
        typer.Option(
            "--backend",
            "-b",
            help="Vector storage backend ('memory' or 'pgvector').",
        ),
    ] = None,
) -> None:
    """
    Ask a question over the indexed knowledge base.
    """
    if backend:
        _, repo, _, ask_uc = get_adapters(backend=backend)
    else:
        _, repo, _, ask_uc = get_adapters()
    backend_name = get_backend_name(repo)

    try:
        req = QueryRequest(question=question, top_k=top_k)
        res = ask_uc.execute(req)

        console.print(
            Panel(
                res.answer,
                title="[bold green]Resposta do Assistente[/bold green]",
                subtitle=(
                    f"Backend: [bold magenta]{backend_name}[/bold magenta] | "
                    f"Fontes: {len(res.sources)}"
                ),
            )
        )

        if res.sources:
            table = Table(title="Fontes / Chunks Recuperados", show_lines=True)
            table.add_column("Score", justify="right", style="cyan", width=10)
            table.add_column("Origem", style="yellow", width=20)
            table.add_column("Conteúdo", style="white")

            for src in res.sources:
                table.add_row(
                    f"{src.score:.4f}",
                    src.source or "N/A",
                    src.content[:150] + ("..." if len(src.content) > 150 else ""),
                )
            console.print(table)
    except Exception as e:
        console.print(f"[bold red]Falha na consulta:[/bold red] {e}")
        raise typer.Exit(code=1) from e


def parse_interactive_ingest(raw_arg: str) -> tuple[str, str | None]:
    """
    Parses arguments for interactive ingest command.
    Supports:
      - ingest -f <filepath> [-s <source>]
      - ingest --file <filepath> [--source <source>]
      - ingest <filepath> (if filepath points to an existing file)
      - ingest -t <text> [-s <source>]
      - ingest <raw text>
    Returns: (content, source_label)
    """
    trimmed = raw_arg.strip()
    if not trimmed:
        raise ValueError("Forneça um caminho de arquivo ou texto para ingestão.")

    try:
        tokens = shlex.split(trimmed)
    except ValueError:
        tokens = trimmed.split()

    file_path: Path | None = None
    text_content: str | None = None
    source_label: str | None = None

    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        if token in ("-f", "--file") and idx + 1 < len(tokens):
            file_path = Path(tokens[idx + 1])
            idx += 2
        elif token in ("-s", "--source") and idx + 1 < len(tokens):
            source_label = tokens[idx + 1]
            idx += 2
        elif token in ("-t", "--text") and idx + 1 < len(tokens):
            text_content = tokens[idx + 1]
            idx += 2
        else:
            # Check if this single positional argument points to an existing file
            candidate = Path(token)
            if file_path is None and text_content is None and candidate.is_file():
                file_path = candidate
                idx += 1
            else:
                # Accumulate the remaining arguments as text
                text_content = " ".join(tokens[idx:])
                break

    if file_path:
        if not file_path.is_file():
            raise FileNotFoundError(f"Arquivo '{file_path}' não encontrado.")
        content = file_path.read_text(encoding="utf-8")
        source = source_label or file_path.name
        return content, source

    if text_content:
        return text_content, source_label or "sessão_interativa"

    # Direct fallback: check if trimmed string is a file path
    candidate = Path(trimmed)
    if candidate.is_file():
        return candidate.read_text(encoding="utf-8"), source_label or candidate.name

    return trimmed, source_label or "sessão_interativa"


@app.command()
def interactive(
    backend: Annotated[
        str | None,
        typer.Option(
            "--backend",
            "-b",
            help="Vector storage backend ('memory' or 'pgvector').",
        ),
    ] = None,
) -> None:
    """
    Start an interactive session where documents can be ingested and queried
    without resetting between commands.
    """
    if backend:
        _, repo, ingest_uc, ask_uc = get_adapters(backend=backend)
    else:
        _, repo, ingest_uc, ask_uc = get_adapters()
    backend_name = get_backend_name(repo)

    panel_text = (
        f"[bold cyan]Modo Interativo RAG Local[/bold cyan] "
        f"[dim](Backend: [bold magenta]{backend_name}[/bold magenta])[/dim]\n\n"
        "Comandos disponíveis:\n"
        "  [yellow]ingest <arquivo>[/yellow] ou "
        "[yellow]ingest -f <arquivo>[/yellow] - Ingestão de arquivo\n"
        "  [yellow]ingest <texto>[/yellow] ou "
        "[yellow]ingest -t <texto>[/yellow]     - Ingestão de texto\n"
        "  [yellow]ask <pergunta>[/yellow]                         "
        " - Fazer uma pergunta sobre o contexto\n"
        "  [yellow]status / count[/yellow]                         "
        " - Ver quantidade de chunks e backend ativo\n"
        "  [yellow]exit / quit[/yellow]                            "
        " - Sair da sessão"
    )
    console.print(Panel.fit(panel_text, title="Bem-vindo ao RAG CLI"))

    while True:
        try:
            user_input = console.input("[bold green]rag-cli>[/bold green] ").strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                console.print("[dim]Encerrando sessão interativa...[/dim]")
                break

            parts = user_input.split(" ", 1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd == "ingest":
                if not arg:
                    console.print(
                        "[red]Uso: ingest <arquivo|texto> "
                        "(ex: ingest docs/pt-br/visao-geral-e-unidades.md)[/red]"
                    )
                    continue

                content, src_label = parse_interactive_ingest(arg)
                req = IngestRequest(content=content, source=src_label)
                res = ingest_uc.execute(req)
                console.print(
                    f"[green]✓ Ingestão concluída ({backend_name}):[/green] "
                    f"[cyan]{res.chunks_count}[/cyan] chunks de "
                    f"[yellow]{src_label}[/yellow] "
                    f"(Total no banco: [bold]{repo.count()}[/bold])"
                )

            elif cmd in ("status", "count"):
                console.print(
                    f"[cyan]Backend ativo:[/cyan] "
                    f"[bold magenta]{backend_name}[/bold magenta] | "
                    f"[cyan]Chunks indexados:[/cyan] [bold]{repo.count()}[/bold]"
                )

            elif cmd == "ask":
                if not arg:
                    console.print("[red]Uso: ask [-k <top_k>] <pergunta>[/red]")
                    continue

                top_k = 4
                question = arg
                if arg.startswith(("-k ", "--top-k ")):
                    parts_q = arg.split(" ", 2)
                    if len(parts_q) >= 3 and parts_q[1].isdigit():
                        top_k = int(parts_q[1])
                        question = parts_q[2]

                req = QueryRequest(question=question, top_k=top_k)
                res = ask_uc.execute(req)
                console.print(f"\n[bold]Resposta:[/bold]\n{res.answer}\n")
                if res.sources:
                    console.print(
                        f"[dim]Fontes recuperadas ({len(res.sources)}):[/dim]"
                    )
                    for s in res.sources:
                        src_str = s.source or "N/A"
                        console.print(
                            f"  • (score: {s.score:.4f}) "
                            f"[{src_str}] {s.content[:70]}..."
                        )

                console.print()

            else:
                console.print(
                    f"[yellow]Comando desconhecido '{cmd}'. "
                    "Use 'ingest', 'ask', 'status' ou 'exit'.[/yellow]"
                )

        except KeyboardInterrupt, EOFError:
            console.print("\n[dim]Sessão finalizada.[/dim]")
            break
        except (ValueError, RuntimeError, OSError) as e:
            console.print(f"[red]Erro:[/red] {e}")


if __name__ == "__main__":
    app()
