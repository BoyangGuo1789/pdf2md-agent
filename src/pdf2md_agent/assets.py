from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .preflight import _fitz, render_pages


def render_all_pages(pdf_path: Path, out_dir: Path, dpi: int = 200) -> list[str]:
    return render_pages(pdf_path, out_dir / "pages", None, dpi=dpi)


def extract_images(pdf_path: Path, out_dir: Path) -> list[dict[str, Any]]:
    fitz = _fitz()
    figures_dir = out_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf_path))
    figures: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for page_no, page in enumerate(doc, start=1):
        for img_no, image in enumerate(page.get_images(full=True), start=1):
            xref = int(image[0])
            if (page_no, xref) in seen:
                continue
            seen.add((page_no, xref))
            try:
                extracted = doc.extract_image(xref)
            except Exception as exc:
                figures.append({"page": page_no, "xref": xref, "warning": f"image_extract_failed: {exc}"})
                continue
            ext = extracted.get("ext", "bin")
            data = extracted.get("image")
            if not data:
                continue
            rel = Path("figures") / f"page_{page_no:04d}_img_{img_no:02d}.{ext}"
            (out_dir / rel).write_bytes(data)
            figures.append({"page": page_no, "xref": xref, "path": str(rel), "ext": ext})
    doc.close()
    return figures


def _table_to_markdown(rows: list[list[Any]]) -> str:
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    normalized = [[("" if cell is None else str(cell)).strip() for cell in row] + [""] * (width - len(row)) for row in rows]
    header = normalized[0]
    body = normalized[1:]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * width) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def extract_tables(pdf_path: Path, out_dir: Path) -> list[dict[str, Any]]:
    fitz = _fitz()
    tables_dir = out_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf_path))
    tables: list[dict[str, Any]] = []
    for page_no, page in enumerate(doc, start=1):
        if not hasattr(page, "find_tables"):
            break
        try:
            found = page.find_tables()
        except Exception as exc:
            tables.append({"page": page_no, "warning": f"table_detection_failed: {exc}"})
            continue
        for table_no, table in enumerate(getattr(found, "tables", []) or [], start=1):
            try:
                rows = table.extract()
            except Exception as exc:
                tables.append({"page": page_no, "table": table_no, "warning": f"table_extract_failed: {exc}"})
                continue
            if not rows:
                continue
            csv_rel = Path("tables") / f"page_{page_no:04d}_table_{table_no:02d}.csv"
            md_rel = Path("tables") / f"page_{page_no:04d}_table_{table_no:02d}.md"
            with (out_dir / csv_rel).open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(rows)
            (out_dir / md_rel).write_text(_table_to_markdown(rows), encoding="utf-8")
            tables.append(
                {
                    "page": page_no,
                    "table": table_no,
                    "csv_path": str(csv_rel),
                    "markdown_path": str(md_rel),
                    "row_count": len(rows),
                }
            )
    doc.close()
    return tables


def extract_assets(pdf_path: Path, out_dir: Path) -> dict[str, list[dict[str, Any]]]:
    return {
        "figures": extract_images(pdf_path, out_dir),
        "tables": extract_tables(pdf_path, out_dir),
    }
