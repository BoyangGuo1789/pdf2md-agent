from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .config import build_config
from .pipeline import batch_convert, convert_pdf
from .preflight import inspect_to_dir

app = typer.Typer(no_args_is_help=True, help="Convert PDFs into page-aware Markdown research bundles.")
console = Console()


def _overrides(
    engine: str,
    ocr: str,
    render_pages: bool,
    extract_assets: bool,
    chunk: bool,
    chunk_size: int,
    chunk_overlap: int,
    strict: bool,
    keep_normalized_pdf: bool,
) -> dict[str, object]:
    return {
        "engine": engine,
        "ocr": ocr,
        "render_pages": render_pages,
        "extract_assets": extract_assets,
        "chunk": chunk,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "strict": strict,
        "keep_normalized_pdf": keep_normalized_pdf,
    }


@app.command()
def inspect(
    input_pdf: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    out: Path = typer.Option(..., "--out", "-o", help="Directory for preflight output."),
    render_dpi: int = typer.Option(200, help="DPI for rendered suspicious pages."),
) -> None:
    """Inspect a PDF and render the first/suspicious pages."""
    preflight = inspect_to_dir(input_pdf, out, dpi=render_dpi)
    console.print(f"[green]Preflight complete[/green]: {preflight['page_count']} pages -> {out}")


@app.command()
def convert(
    input_pdf: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    out: Path = typer.Option(..., "--out", "-o", help="Output bundle directory."),
    engine: str = typer.Option("auto", help="auto|pymupdf4llm|docling|marker|text"),
    ocr: str = typer.Option("auto", help="auto|never|always"),
    render_pages: bool = typer.Option(True, "--render-pages/--no-render-pages", help="Render page PNGs."),
    extract_assets: bool = typer.Option(True, "--extract-assets/--no-extract-assets", help="Extract images and tables."),
    chunk: bool = typer.Option(True, "--chunk/--no-chunk", help="Write chunks/chunks.jsonl."),
    chunk_size: int = typer.Option(1200, help="Target chunk size in characters."),
    chunk_overlap: int = typer.Option(150, help="Chunk overlap in characters."),
    strict: bool = typer.Option(False, "--strict", help="Fail when validation has warnings."),
    keep_normalized_pdf: bool = typer.Option(False, "--keep-normalized-pdf", help="Keep OCR-normalized PDF."),
    config: Optional[Path] = typer.Option(None, "--config", exists=True, dir_okay=False, readable=True),
) -> None:
    """Convert a single PDF into a Markdown research bundle."""
    manifest = convert_pdf(
        input_pdf,
        out,
        config,
        _overrides(engine, ocr, render_pages, extract_assets, chunk, chunk_size, chunk_overlap, strict, keep_normalized_pdf),
    )
    status = manifest["validation"]["status"]
    color = "green" if status == "pass" else "yellow" if status == "warn" else "red"
    console.print(f"[{color}]Conversion {status}[/{color}]: {out}")
    if strict and status != "pass":
        raise typer.Exit(1)


@app.command()
def batch(
    input_dir: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
    out: Path = typer.Option(..., "--out", "-o", help="Output parent directory."),
    engine: str = typer.Option("auto", help="auto|pymupdf4llm|docling|marker|text"),
    ocr: str = typer.Option("auto", help="auto|never|always"),
    jobs: int = typer.Option(1, help="Reserved for future parallel execution."),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing output subdirectories."),
    render_pages: bool = typer.Option(True, "--render-pages/--no-render-pages", help="Render page PNGs."),
    extract_assets: bool = typer.Option(True, "--extract-assets/--no-extract-assets", help="Extract images and tables."),
    chunk: bool = typer.Option(True, "--chunk/--no-chunk", help="Write chunks/chunks.jsonl."),
    chunk_size: int = typer.Option(1200, help="Target chunk size in characters."),
    chunk_overlap: int = typer.Option(150, help="Chunk overlap in characters."),
    strict: bool = typer.Option(False, "--strict", help="Fail when validation has warnings."),
    keep_normalized_pdf: bool = typer.Option(False, "--keep-normalized-pdf", help="Keep OCR-normalized PDF."),
    config: Optional[Path] = typer.Option(None, "--config", exists=True, dir_okay=False, readable=True),
) -> None:
    """Recursively convert PDFs under a directory."""
    if jobs != 1:
        console.print("[yellow]--jobs is accepted but this version runs sequentially.[/yellow]")
    summary = batch_convert(
        input_dir,
        out,
        config,
        _overrides(engine, ocr, render_pages, extract_assets, chunk, chunk_size, chunk_overlap, strict, keep_normalized_pdf),
        overwrite=overwrite,
    )
    console.print(f"[green]Batch complete[/green]: {len(summary['outputs'])} PDFs -> {out / 'batch_summary.json'}")


@app.command()
def config_defaults() -> None:
    """Print the effective default config."""
    import json

    console.print(json.dumps(build_config(None, {}), ensure_ascii=False, indent=2))
