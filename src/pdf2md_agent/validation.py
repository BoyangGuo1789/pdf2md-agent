from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .markdown import PAGE_ANCHOR_RE, extract_page_sections, local_markdown_links


def _check(status: str, name: str, detail: str, **extra: Any) -> dict[str, Any]:
    row = {"name": name, "status": status, "detail": detail}
    row.update(extra)
    return row


def _page_text_chars(section: str) -> int:
    text = re.sub(r"<!--.*?-->", "", section, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[[^\]]*\]\([^)]+\)", "", text)
    return len(text.strip())


def validate_bundle(
    out_dir: Path,
    markdown: str,
    preflight: dict[str, Any],
    chunk_path: Path | None,
    strict: bool = False,
    coverage_ratio_warn: float = 0.5,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    page_count = int(preflight.get("page_count", 0))
    anchors = [int(m.group(1)) for m in PAGE_ANCHOR_RE.finditer(markdown)]
    if len(anchors) == page_count and sorted(anchors) == list(range(1, page_count + 1)):
        checks.append(_check("pass", "page_count", f"{len(anchors)} page anchors found for {page_count} pages"))
    else:
        checks.append(_check("fail", "page_count", f"{len(anchors)} page anchors found for {page_count} pages"))

    sections = dict(extract_page_sections(markdown))
    for page in preflight.get("pages", []):
        page_no = int(page["page"])
        preflight_chars = int(page.get("char_count", 0))
        markdown_chars = _page_text_chars(sections.get(page_no, ""))
        if preflight_chars > 500 and markdown_chars < coverage_ratio_warn * preflight_chars:
            checks.append(
                _check(
                    "warn",
                    "coverage",
                    "Markdown chars much lower than preflight chars",
                    page=page_no,
                    char_count_preflight=preflight_chars,
                    char_count_markdown=markdown_chars,
                )
            )
        if preflight_chars > 0 and markdown_chars == 0 and not page.get("is_probably_scanned"):
            checks.append(_check("warn", "empty_page", "Empty Markdown page where preflight found text", page=page_no))

    missing_links = []
    for link in local_markdown_links(markdown):
        normalized = link[2:] if link.startswith("./") else link
        if normalized and not (out_dir / normalized).exists():
            missing_links.append(link)
    if missing_links:
        checks.append(_check("fail", "asset_links", "Missing local Markdown links", missing_links=missing_links))
    else:
        checks.append(_check("pass", "asset_links", "All local Markdown links exist"))

    if chunk_path is not None:
        bad_chunks = 0
        if not chunk_path.exists():
            checks.append(_check("fail", "chunks", f"Missing chunks file: {chunk_path.relative_to(out_dir)}"))
        else:
            with chunk_path.open("r", encoding="utf-8") as f:
                for line_no, line in enumerate(f, start=1):
                    if not line.strip():
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        bad_chunks += 1
                        continue
                    required = ["source_sha256", "page_start", "page_end", "text"]
                    if any(not row.get(field) for field in required):
                        bad_chunks += 1
            if bad_chunks:
                checks.append(_check("fail", "chunks", f"{bad_chunks} invalid chunks"))
            else:
                checks.append(_check("pass", "chunks", "Every chunk has source hash and page span"))

    has_fail = any(c["status"] == "fail" for c in checks)
    has_warn = any(c["status"] == "warn" for c in checks)
    status = "fail" if has_fail or (strict and has_warn) else "warn" if has_warn else "pass"
    return {"status": status, "checks": checks}
