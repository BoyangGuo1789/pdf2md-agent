from __future__ import annotations

from pathlib import Path
from typing import Any

from .assets import extract_assets, render_all_pages
from .chunking import build_chunks, write_chunks
from .config import build_config
from .engines import get_engine
from .manifest import build_manifest
from .markdown import append_asset_references, document_header, title_from_pdf_path
from .ocr import maybe_ocr_pdf
from .preflight import inspect_pdf
from .utils import safe_slug, write_json
from .validation import validate_bundle


def convert_pdf(pdf_path: Path, out_dir: Path, config_path: Path | None = None, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    config = build_config(config_path, overrides or {})
    pdf_path = pdf_path.expanduser().resolve()
    out_dir = out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "logs").mkdir(exist_ok=True)

    preflight = inspect_pdf(pdf_path)
    write_json(out_dir / "logs" / "preflight.json", preflight)

    conversion_pdf, ocr_info, ocr_warnings = maybe_ocr_pdf(pdf_path, out_dir, preflight, config)

    engine = get_engine(config.get("engine", "auto"), config.get("engines", {}).get("prefer"))
    if not engine.is_available():
        raise RuntimeError(f"Requested engine '{config.get('engine')}' is not available.")
    result = engine.convert(conversion_pdf, out_dir, config)

    render_dpi = int(config.get("validation", {}).get("render_dpi", 200))
    if config.get("render_pages", True):
        render_all_pages(conversion_pdf, out_dir, dpi=render_dpi)

    assets = {"figures": [], "tables": []}
    if config.get("extract_assets", True):
        assets = extract_assets(conversion_pdf, out_dir)

    source_name = pdf_path.name
    title = title_from_pdf_path(pdf_path, preflight.get("metadata", {}).get("title"))
    markdown = document_header(title, source_name, preflight["sha256"], result.engine) + result.markdown.strip() + "\n"
    markdown = append_asset_references(markdown, assets)
    (out_dir / "document.md").write_text(markdown, encoding="utf-8")

    document_json = {
        "source_pdf": str(pdf_path),
        "source_sha256": preflight["sha256"],
        "engine": result.engine,
        **result.document_json,
        "assets": assets,
    }
    write_json(out_dir / "document.json", document_json)

    chunks_path = None
    if config.get("chunk", True):
        chunks = build_chunks(
            markdown,
            source_pdf=source_name,
            source_sha256=preflight["sha256"],
            chunk_size=int(config.get("chunk_size", 1200)),
            chunk_overlap=int(config.get("chunk_overlap", 150)),
        )
        chunks_path = out_dir / "chunks" / "chunks.jsonl"
        write_chunks(chunks, chunks_path)

    validation = validate_bundle(
        out_dir,
        markdown,
        preflight,
        chunks_path,
        strict=bool(config.get("strict", False)),
        coverage_ratio_warn=float(config.get("validation", {}).get("coverage_ratio_warn", 0.5)),
    )
    write_json(out_dir / "logs" / "validation.json", validation)

    manifest = build_manifest(
        pdf_path,
        preflight,
        result.engine,
        ocr_info,
        validation,
        [*ocr_warnings, *result.warnings],
        assets,
        chunks_path,
    )
    write_json(out_dir / "manifest.json", manifest)

    if ocr_info.get("normalized_pdf") and not config.get("keep_normalized_pdf", False):
        normalized_path = Path(str(ocr_info["normalized_pdf"]))
        if normalized_path.exists():
            normalized_path.unlink()

    return manifest


def batch_convert(
    input_dir: Path,
    out_dir: Path,
    config_path: Path | None,
    overrides: dict[str, Any],
    overwrite: bool = False,
) -> dict[str, Any]:
    input_dir = input_dir.expanduser().resolve()
    out_dir = out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = {"input_dir": str(input_dir), "outputs": []}
    for pdf_path in sorted(input_dir.rglob("*.pdf")):
        slug = safe_slug(pdf_path.stem)
        target = out_dir / slug
        if target.exists() and not overwrite:
            summary["outputs"].append({"source_pdf": str(pdf_path), "out_dir": str(target), "status": "skipped_exists"})
            continue
        try:
            manifest = convert_pdf(pdf_path, target, config_path, overrides)
            summary["outputs"].append(
                {
                    "source_pdf": str(pdf_path),
                    "out_dir": str(target),
                    "status": manifest["validation"]["status"],
                }
            )
        except Exception as exc:
            summary["outputs"].append({"source_pdf": str(pdf_path), "out_dir": str(target), "status": "error", "error": str(exc)})
    write_json(out_dir / "batch_summary.json", summary)
    return summary
