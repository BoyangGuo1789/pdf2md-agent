from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any


def preflight_needs_ocr(preflight: dict[str, Any]) -> bool:
    pages = preflight.get("pages", [])
    if not pages:
        return False
    scanned = [p for p in pages if p.get("is_probably_scanned") or p.get("char_count", 0) == 0]
    return len(scanned) / len(pages) >= 0.25


def maybe_ocr_pdf(
    pdf_path: Path,
    out_dir: Path,
    preflight: dict[str, Any],
    config: dict[str, Any],
) -> tuple[Path, dict[str, Any], list[str]]:
    mode = config.get("ocr", "auto")
    warnings: list[str] = []
    info: dict[str, Any] = {"mode": mode, "ran": False, "command": None, "normalized_pdf": None}
    if mode == "never":
        return pdf_path, info, warnings
    if mode == "auto" and not preflight_needs_ocr(preflight):
        return pdf_path, info, warnings
    if mode not in {"auto", "always"}:
        raise ValueError(f"Unknown OCR mode '{mode}'. Expected auto, never, or always.")

    if shutil.which("ocrmypdf") is None:
        message = "ocrmypdf_missing: install OCRmyPDF and Tesseract to OCR scanned PDFs"
        if mode == "always" or config.get("strict"):
            raise RuntimeError(message)
        warnings.append(message)
        return pdf_path, info, warnings

    normalized = out_dir / "logs" / "normalized.pdf"
    normalized.parent.mkdir(parents=True, exist_ok=True)
    languages = str(config.get("ocr_languages", "eng"))
    cmd = [
        "ocrmypdf",
        "--skip-text",
        "--deskew",
        "--clean",
        "-l",
        languages,
        str(pdf_path),
        str(normalized),
    ]
    info["command"] = cmd
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    info["returncode"] = proc.returncode
    info["stderr"] = proc.stderr[-4000:]
    info["stdout"] = proc.stdout[-4000:]
    if proc.returncode != 0:
        warning = f"ocr_failed_exit_{proc.returncode}"
        if config.get("strict"):
            raise RuntimeError(warning)
        warnings.append(warning)
        return pdf_path, info, warnings

    info["ran"] = True
    info["normalized_pdf"] = str(normalized)
    if not config.get("keep_normalized_pdf", False):
        info["normalized_pdf_retained"] = False
    else:
        info["normalized_pdf_retained"] = True
    return normalized, info, warnings
