from __future__ import annotations

import re
from pathlib import Path


PAGE_ANCHOR_RE = re.compile(r'<a\s+id=["\']page-(\d+)["\']\s*></a>', re.IGNORECASE)


def page_heading(page_no: int, body: str, warning: str | None = None) -> str:
    parts = [f'<a id="page-{page_no}"></a>', "", f"## Page {page_no}", ""]
    if warning:
        parts.extend([f"<!-- warning: {warning} -->", ""])
    parts.append(body.strip())
    return "\n".join(parts).rstrip() + "\n"


def document_header(title: str, source_pdf: str, sha256: str, engine: str) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            f"<!-- source: {source_pdf} -->",
            f"<!-- sha256: {sha256} -->",
            f"<!-- engine: {engine} -->",
            "",
        ]
    )


def extract_page_sections(markdown: str) -> list[tuple[int, str]]:
    matches = list(PAGE_ANCHOR_RE.finditer(markdown))
    sections: list[tuple[int, str]] = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        sections.append((int(match.group(1)), markdown[start:end]))
    return sections


def local_markdown_links(markdown: str) -> list[str]:
    links = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", markdown)
    local: list[str] = []
    for link in links:
        if link.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if link.lower().startswith("data:"):
            continue
        local.append(link.split("#", 1)[0])
    return local


def append_asset_references(markdown: str, assets: dict[str, list[dict[str, object]]]) -> str:
    if not assets:
        return markdown
    by_page: dict[int, list[str]] = {}
    for image in assets.get("figures", []):
        page = int(image.get("page", 0))
        rel = str(image.get("path", ""))
        if page and rel:
            by_page.setdefault(page, []).append(f"![Figure p{page}](./{rel})")
    for table in assets.get("tables", []):
        page = int(table.get("page", 0))
        csv_path = str(table.get("csv_path", ""))
        md_path = str(table.get("markdown_path", ""))
        if page and csv_path:
            line = f"Table p{page}: [CSV](./{csv_path})"
            if md_path:
                line += f" | [Markdown](./{md_path})"
            by_page.setdefault(page, []).append(line)

    if not by_page:
        return markdown

    sections = extract_page_sections(markdown)
    if not sections:
        return markdown

    prefix = markdown[: PAGE_ANCHOR_RE.search(markdown).start()]  # type: ignore[union-attr]
    rendered = [prefix.rstrip(), ""]
    for page_no, section in sections:
        section = section.rstrip()
        rendered.append(section)
        refs = by_page.get(page_no)
        if refs:
            rendered.extend(["", *refs])
        rendered.append("")
    return "\n".join(rendered).rstrip() + "\n"


def title_from_pdf_path(path: str | Path, metadata_title: str | None = None) -> str:
    if metadata_title and metadata_title.strip():
        return metadata_title.strip()
    return Path(path).stem
