from __future__ import annotations

from pathlib import Path
from typing import Any

from .utils import import_error_hint, sha256_file, write_json


def _fitz():
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(import_error_hint("pymupdf", "fitz")) from exc
    return fitz


def inspect_pdf(path: str | Path) -> dict[str, Any]:
    fitz = _fitz()
    pdf_path = Path(path)
    doc = fitz.open(str(pdf_path))
    result: dict[str, Any] = {
        "source_pdf": str(pdf_path),
        "sha256": sha256_file(pdf_path),
        "page_count": doc.page_count,
        "encrypted": bool(getattr(doc, "needs_pass", False) or getattr(doc, "is_encrypted", False)),
        "metadata": doc.metadata or {},
        "pages": [],
        "document_warnings": [],
    }

    if result["encrypted"]:
        result["document_warnings"].append("pdf_is_encrypted_or_password_protected")

    for page_no, page in enumerate(doc, start=1):
        text = page.get_text("text") or ""
        words = page.get_text("words") or []
        images = page.get_images(full=True) or []
        try:
            drawings = page.get_drawings() or []
        except Exception:
            drawings = []

        is_probably_scanned = len(words) < 20 and len(images) >= 1
        warnings: list[str] = []
        if not text.strip():
            warnings.append("no_text_extracted")
        if is_probably_scanned:
            warnings.append("probably_scanned")

        result["pages"].append(
            {
                "page": page_no,
                "width": float(page.rect.width),
                "height": float(page.rect.height),
                "word_count": len(words),
                "char_count": len(text),
                "image_count": len(images),
                "drawing_count": len(drawings),
                "is_probably_scanned": is_probably_scanned,
                "warnings": warnings,
            }
        )
    doc.close()
    return result


def suspicious_page_numbers(preflight: dict[str, Any]) -> list[int]:
    pages = preflight.get("pages", [])
    selected = {1} if pages else set()
    for page in pages:
        if page.get("is_probably_scanned") or page.get("char_count", 0) == 0:
            selected.add(int(page["page"]))
    for prev_page, page, next_page in zip(pages, pages[1:], pages[2:]):
        neighbor_chars = (prev_page.get("char_count", 0) + next_page.get("char_count", 0)) / 2
        if neighbor_chars > 500 and page.get("char_count", 0) < 0.25 * neighbor_chars:
            selected.add(int(page["page"]))
    return sorted(selected)


def render_pages(
    pdf_path: str | Path,
    pages_dir: str | Path,
    page_numbers: list[int] | None = None,
    dpi: int = 200,
) -> list[str]:
    fitz = _fitz()
    pdf_path = Path(pdf_path)
    pages_dir = Path(pages_dir)
    pages_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    selected = page_numbers or list(range(1, doc.page_count + 1))
    written: list[str] = []
    for page_no in selected:
        if page_no < 1 or page_no > doc.page_count:
            continue
        page = doc.load_page(page_no - 1)
        pix = page.get_pixmap(dpi=dpi, alpha=False)
        rel = Path("pages") / f"page_{page_no:04d}.png"
        out_path = pages_dir / rel.name
        pix.save(str(out_path))
        written.append(str(rel))
    doc.close()
    return written


def inspect_to_dir(pdf_path: Path, out_dir: Path, dpi: int = 200) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    preflight = inspect_pdf(pdf_path)
    write_json(out_dir / "preflight.json", preflight)
    render_pages(pdf_path, out_dir / "pages", suspicious_page_numbers(preflight), dpi=dpi)
    return preflight
