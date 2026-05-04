from __future__ import annotations

from pathlib import Path
from typing import Any

from . import __version__
from .utils import utc_now_iso


def build_manifest(
    source_pdf: Path,
    preflight: dict[str, Any],
    engine: str,
    ocr_info: dict[str, Any],
    validation: dict[str, Any],
    conversion_warnings: list[str],
    assets: dict[str, list[dict[str, Any]]] | None,
    chunks_path: Path | None,
) -> dict[str, Any]:
    warnings = list(preflight.get("document_warnings", []))
    warnings.extend(conversion_warnings)
    for group in (assets or {}).values():
        warnings.extend(str(item["warning"]) for item in group if "warning" in item)

    outputs: dict[str, Any] = {
        "markdown": "document.md",
        "json": "document.json",
        "pages_dir": "pages",
        "figures_dir": "figures",
        "tables_dir": "tables",
    }
    if chunks_path is not None:
        outputs["chunks"] = "chunks/chunks.jsonl"

    return {
        "schema_version": "0.1.0",
        "source_pdf": str(source_pdf),
        "source_sha256": preflight["sha256"],
        "created_at_utc": utc_now_iso(),
        "tool_version": __version__,
        "engine": engine,
        "ocr_mode": ocr_info.get("mode"),
        "normalized_pdf": ocr_info.get("normalized_pdf"),
        "page_count": preflight["page_count"],
        "outputs": outputs,
        "page_stats": [
            {
                "page": p["page"],
                "char_count_preflight": p.get("char_count", 0),
                "word_count_preflight": p.get("word_count", 0),
                "is_probably_scanned": p.get("is_probably_scanned", False),
                "warnings": p.get("warnings", []),
            }
            for p in preflight.get("pages", [])
        ],
        "assets": assets or {"figures": [], "tables": []},
        "warnings": warnings,
        "validation": validation,
        "ocr": ocr_info,
    }
