from __future__ import annotations

from pathlib import Path
from typing import Any

from ..markdown import page_heading
from ..preflight import _fitz
from .base import ConversionResult


class TextEngine:
    name = "text"

    def is_available(self) -> bool:
        try:
            _fitz()
            return True
        except RuntimeError:
            return False

    def convert(self, pdf_path: Path, out_dir: Path, config: dict[str, Any]) -> ConversionResult:
        fitz = _fitz()
        doc = fitz.open(str(pdf_path))
        sections: list[str] = []
        pages: list[dict[str, Any]] = []
        warnings = ["fallback_text_engine_used"]
        for page_no, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            warning = None
            if not text.strip():
                warning = f"no extractable text on this page; see pages/page_{page_no:04d}.png"
            sections.append(page_heading(page_no, text, warning))
            pages.append({"page": page_no, "text": text, "char_count": len(text)})
        doc.close()
        return ConversionResult(
            markdown="\n".join(sections).strip() + "\n",
            document_json={"pages": pages},
            engine=self.name,
            warnings=warnings,
        )
