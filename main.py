"""
main.py — GMC Extractor CLI
Usage:
  python main.py run samples/policy.pdf
  python main.py run-all samples/
  python main.py inspect samples/policy.pdf
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

# Reconfigure stdout/stderr to UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import os
# Fix httpx bug where unbracketed IPv6 entries like '::1' in NO_PROXY cause InvalidURL: Invalid port: ':1'
for _var in ("NO_PROXY", "no_proxy"):
    _val = os.environ.get(_var)
    if _val:
        os.environ[_var] = ",".join([e.strip() for e in _val.split(",") if ":" not in e and e.strip()])

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="gmc-extractor",
    help="Extract structured data from GMC insurance policy PDFs.",
    no_args_is_help=True,
)
console = Console()


def _setup(verbose: bool, provider: Optional[str], model: Optional[str], no_cache: bool, max_requests: Optional[int]):
    """Common setup: logging, settings, LLM client."""
    from gmc_extractor.logging_utils import setup_logging
    from gmc_extractor.config import get_settings
    from gmc_extractor.llm.factory import get_client

    level = "DEBUG" if verbose else "INFO"
    setup_logging(level)

    settings = get_settings()

    # Apply CLI overrides
    if max_requests is not None:
        settings.max_requests_per_run = max_requests

    try:
        client = get_client(
            settings,
            use_cache=not no_cache,
            provider_override=provider,
            model_override=model,
        )
    except (ValueError, RuntimeError) as exc:
        console.print(f"[bold red]Configuration error:[/bold red] {exc}")
        raise typer.Exit(1)
    return settings, client


@app.command()
def run(
    pdf_path: Path = typer.Argument(..., help="Path to a single PDF file."),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="LLM provider: gemini, openai, ollama, or mock."),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Override model name."),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass disk cache."),
    max_requests: Optional[int] = typer.Option(None, "--max-requests", help="Max LLM requests for this run."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable DEBUG logging."),
) -> None:
    """Process a single PDF and write JSON/CSV/report to output/."""
    if not pdf_path.exists():
        console.print(f"[red]File not found: {pdf_path}[/red]")
        raise typer.Exit(1)

    settings, client = _setup(verbose, provider, model, no_cache, max_requests)

    from gmc_extractor.pipeline import run_pdf

    with console.status(f"[cyan]Processing {pdf_path.name}...[/cyan]"):
        result = run_pdf(pdf_path, client, settings, use_cache=not no_cache)

    _print_summary_table([result], settings)


@app.command(name="run-all")
def run_all(
    folder: Path = typer.Argument(..., help="Path to a folder containing PDF files."),
    provider: Optional[str] = typer.Option(None, "--provider", "-p"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
    no_cache: bool = typer.Option(False, "--no-cache"),
    max_requests: Optional[int] = typer.Option(None, "--max-requests"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Process all PDFs in a folder."""
    if not folder.is_dir():
        console.print(f"[red]Not a directory: {folder}[/red]")
        raise typer.Exit(1)

    settings, client = _setup(verbose, provider, model, no_cache, max_requests)

    from gmc_extractor.pipeline import run_batch

    results = run_batch(folder, client, settings, use_cache=not no_cache)
    _print_summary_table(results, settings)


@app.command()
def inspect(
    pdf_path: Path = typer.Argument(..., help="Path to a PDF to inspect."),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """
    Print diagnostic info about a PDF:
    page count, scanned pages, section headings.
    """
    from gmc_extractor.logging_utils import setup_logging
    from gmc_extractor.config import get_settings
    from gmc_extractor.pdf.reader import read_pdf
    from gmc_extractor.pdf.cleaner import clean_pages

    setup_logging("DEBUG" if verbose else "INFO")
    settings = get_settings()

    if not pdf_path.exists():
        console.print(f"[red]File not found: {pdf_path}[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold cyan]Inspecting:[/bold cyan] {pdf_path}")
    pages = read_pdf(pdf_path, cache_dir=None, ocr_available=True)
    pages = clean_pages(pages)

    scanned = [p.page_num for p in pages if p.is_scanned]
    console.print(f"  Total pages : [bold]{len(pages)}[/bold]")
    console.print(f"  Scanned     : [yellow]{len(scanned)}[/yellow] {scanned[:10]}")

    # Collect headings
    all_headings: list[tuple[int, str]] = []
    for p in pages:
        for h in p.headings:
            all_headings.append((p.page_num, h))

    console.print(f"  Headings    : {len(all_headings)}")
    if all_headings:
        tbl = Table("Page", "Heading", show_header=True)
        for pg, h in all_headings[:30]:
            tbl.add_row(str(pg), h[:80])
        console.print(tbl)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host interface to bind to."),
    port: int = typer.Option(8000, "--port", "-p", help="Port to listen on."),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable reload on changes."),
) -> None:
    """Start the GMC Extractor API and Dashboard server."""
    from server import run_server
    console.print(f"[bold green]Starting GMC Extractor Server on http://{host}:{port}[/bold green]")
    run_server(host=host, port=port, reload=reload)


def _print_summary_table(results: list, settings) -> None:
    """Print a Rich summary table of extraction results."""
    from gmc_extractor.schema.output import ExtractionResult

    tbl = Table("PDF", "Pages", "Confidence", "Warnings", "Output", show_header=True, header_style="bold cyan")
    for r in results:
        if not isinstance(r, ExtractionResult):
            continue
        stem = settings.output_dir / r.document_info.file_name.replace(".pdf", "")
        conf_color = "green" if r.overall_confidence >= 0.7 else "yellow" if r.overall_confidence >= 0.4 else "red"
        tbl.add_row(
            r.document_info.file_name,
            str(r.document_info.total_pages),
            f"[{conf_color}]{r.overall_confidence:.0%}[/{conf_color}]",
            str(len(r.warnings)),
            str(settings.output_dir),
        )
    console.print()
    console.print(tbl)
    console.print()


if __name__ == "__main__":
    app()

