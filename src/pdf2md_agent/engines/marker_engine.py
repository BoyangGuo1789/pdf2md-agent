from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from ..markdown import page_heading
from ..preflight import _fitz
from .base import ConversionResult


class MarkerEngine:
    name = "marker"

    def is_available(self) -> bool:
        return shutil.which("marker_single") is not None

    def convert(self, pdf_path: Path, out_dir: Path, config: dict[str, Any]) -> ConversionResult:
        marker_cli = config.get("engines", {}).get("marker_cli", "marker_single")
        if shutil.which(marker_cli) is None:
            raise RuntimeError(f"Marker CLI '{marker_cli}' was not found on PATH.")

        marker_out = out_dir / "logs" / "marker"
        marker_out.mkdir(parents=True, exist_ok=True)
        cmd = [marker_cli, str(pdf_path), "--output_dir", str(marker_out)]
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"Marker failed with exit code {proc.returncode}: {proc.stderr.strip()}")

        candidates = sorted(marker_out.rglob("*.md"))
        if not candidates:
            raise RuntimeError("Marker finished but did not produce a Markdown file.")

        markdown = candidates[0].read_text(encoding="utf-8")
        fitz = _fitz()
        doc = fitz.open(str(pdf_path))
        anchors = "\n".join(page_heading(i, "") for i in range(1, doc.page_count + 1))
        doc.close()
        return ConversionResult(
            markdown=anchors.rstrip() + "\n\n" + markdown.strip() + "\n",
            document_json={"marker_output_dir": str(marker_out)},
            engine=self.name,
            warnings=["marker_page_anchors_are_best_effort"],
        )
