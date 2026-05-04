from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "engine": "auto",
    "ocr": "auto",
    "ocr_languages": "eng",
    "render_pages": True,
    "extract_assets": True,
    "chunk": True,
    "chunk_size": 1200,
    "chunk_overlap": 150,
    "strict": False,
    "keep_normalized_pdf": False,
    "engines": {
        "prefer": ["pymupdf4llm", "docling", "text"],
        "marker_cli": "marker_single",
        "grobid_url": "http://localhost:8070",
    },
    "validation": {
        "coverage_ratio_warn": 0.5,
        "render_dpi": 200,
    },
}


def deep_merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        elif value is not None:
            result[key] = value
    return result


def load_config(path: Path | None) -> dict[str, Any]:
    if path is None:
        return deepcopy(DEFAULT_CONFIG)
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("YAML config requires PyYAML. Install with: python -m pip install pyyaml") from exc

    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Config file must contain a mapping: {path}")
    return deep_merge(DEFAULT_CONFIG, loaded)


def build_config(path: Path | None, overrides: dict[str, Any]) -> dict[str, Any]:
    return deep_merge(load_config(path), overrides)
