from __future__ import annotations

from pathlib import Path
from typing import Any

from ..markdown import page_heading
from ..preflight import _fitz
from .base import ConversionResult


class DoclingEngine:
    name = "docling"

    def is_available(self) -> bool:
        try:
            from docling.document_converter import DocumentConverter  # noqa: F401

            return True
        except Exception:
            return False

    def convert(self, pdf_path: Path, out_dir: Path, config: dict[str, Any]) -> ConversionResult:
        try:
            from docling.document_converter import DocumentConverter
        except ImportError as exc:
            raise RuntimeError("Docling is not installed. Install with: python -m pip install 'pdf2md-agent[docling]'") from exc

        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))
        markdown = result.document.export_to_markdown()
        document_json: dict[str, Any]
        try:
            document_json = result.document.export_to_dict()
        except Exception:
            document_json = {"docling_export": "dict_export_unavailable"}

        fitz = _fitz()
        doc = fitz.open(str(pdf_path))
        sections = []
        for page_no in range(1, doc.page_count + 1):
            sections.append(page_heading(page_no, ""))
        doc.close()
        anchored = "\n".join(sections).rstrip() + "\n\n" + markdown.strip() + "\n"
        return ConversionResult(markdown=anchored, document_json=document_json, engine=self.name, warnings=[])
