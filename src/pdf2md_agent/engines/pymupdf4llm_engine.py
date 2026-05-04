from __future__ import annotations

from pathlib import Path
from typing import Any

from ..markdown import page_heading
from ..preflight import _fitz
from .base import ConversionResult
from .text_engine import TextEngine


class PyMuPDF4LLMEngine:
    name = "pymupdf4llm"

    def is_available(self) -> bool:
        try:
            import pymupdf4llm  # noqa: F401

            _fitz()
            return True
        except Exception:
            return False

    def convert(self, pdf_path: Path, out_dir: Path, config: dict[str, Any]) -> ConversionResult:
        try:
            import pymupdf4llm
        except ImportError:
            return TextEngine().convert(pdf_path, out_dir, config)

        fitz = _fitz()
        doc = fitz.open(str(pdf_path))
        sections: list[str] = []
        pages: list[dict[str, Any]] = []
        warnings: list[str] = []
        try:
            for page_index in range(doc.page_count):
                try:
                    md = pymupdf4llm.to_markdown(str(pdf_path), pages=[page_index])
                except TypeError as exc:
                    warnings.append(f"pymupdf4llm_page_mode_unavailable: {exc}")
                    fallback = TextEngine().convert(pdf_path, out_dir, config)
                    fallback.warnings.extend(warnings)
                    return fallback
                except Exception as exc:
                    warnings.append(f"pymupdf4llm_page_{page_index + 1}_failed: {exc}")
                    fallback = TextEngine().convert(pdf_path, out_dir, config)
                    fallback.warnings.extend(warnings)
                    return fallback

                text = (md or "").strip()
                warning = None
                if not text:
                    warning = f"no extractable text on this page; see pages/page_{page_index + 1:04d}.png"
                sections.append(page_heading(page_index + 1, text, warning))
                pages.append({"page": page_index + 1, "markdown": text, "char_count": len(text)})
        finally:
            doc.close()

        return ConversionResult(
            markdown="\n".join(sections).strip() + "\n",
            document_json={"pages": pages},
            engine=self.name,
            warnings=warnings,
        )
