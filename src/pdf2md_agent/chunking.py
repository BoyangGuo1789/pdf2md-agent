from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .markdown import extract_page_sections


def _strip_noise(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r'<a\s+id=["\']page-\d+["\']\s*></a>', "", text)
    text = re.sub(r"(?m)^##\s+Page\s+\d+\s*$", "", text)
    return text.strip()


def _split_paragraphs(text: str) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if paragraphs:
        return paragraphs
    return [text.strip()] if text.strip() else []


def build_chunks(
    markdown: str,
    source_pdf: str,
    source_sha256: str,
    chunk_size: int = 1200,
    chunk_overlap: int = 150,
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    chunk_no = 1
    for page_no, section in extract_page_sections(markdown):
        for paragraph in _split_paragraphs(_strip_noise(section)):
            if len(paragraph) <= chunk_size:
                pieces = [paragraph]
            else:
                pieces = []
                start = 0
                step = max(1, chunk_size - chunk_overlap)
                while start < len(paragraph):
                    pieces.append(paragraph[start : start + chunk_size].strip())
                    start += step

            for piece in pieces:
                if not piece:
                    continue
                chunks.append(
                    {
                        "id": f"{source_sha256}:p{page_no:04d}:c{chunk_no:04d}",
                        "source_pdf": source_pdf,
                        "source_sha256": source_sha256,
                        "page_start": page_no,
                        "page_end": page_no,
                        "text": piece,
                        "markdown_path": "document.md",
                        "anchors": [f"page-{page_no}"],
                        "char_count": len(piece),
                        "token_estimate": max(1, len(piece) // 4),
                    }
                )
                chunk_no += 1
    return chunks


def write_chunks(chunks: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
