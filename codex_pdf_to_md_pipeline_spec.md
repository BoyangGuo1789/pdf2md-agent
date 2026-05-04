# Codex Task: Build a Reusable PDF-to-Markdown Ingestion Pipeline for AI/Agent Research

## Goal

Build a reusable local tool that converts PDF files into an LLM/Agent-friendly research bundle:

```text
<output_dir>/
  document.md                 # main Markdown, page-aware, source-traceable
  document.json               # structured document representation when available
  manifest.json               # provenance, hashes, page stats, engine info, warnings
  pages/                      # rendered page images for visual verification and multimodal fallback
    page_0001.png
  figures/                    # extracted or cropped figures/images
  tables/                     # extracted tables as CSV + Markdown
  chunks/                     # retrieval-ready chunks with page spans and stable IDs
    chunks.jsonl
  logs/
    preflight.json
    validation.json
```

The tool must not simply call one PDF parser and trust the result. It must follow this pipeline:

```text
preflight -> optional OCR normalization -> layout-aware conversion -> asset extraction -> chunking -> validation -> bundle output
```

The main purpose is to support downstream AI auto-research: summarization, citation-aware Q&A, paper comparison, literature review, and retrieval-augmented generation.

---

## Key Design Principles

1. **Markdown is the default downstream format, not the only source of truth.**
   - `document.md` is optimized for LLM reading.
   - `document.json`, page PNGs, tables, figures, and `manifest.json` preserve information Markdown may lose.

2. **Every answerable text span should be traceable back to the original PDF page.**
   - Insert explicit page anchors in Markdown.
   - Each chunk must include `page_start`, `page_end`, and source path.

3. **Do not rely on a single parser for all PDFs.**
   - Use a default engine for normal papers.
   - Add optional engines for difficult layouts, tables, equations, and scanned pages.
   - Always save validation signals and warnings.

4. **No LLM calls by default.**
   - The core converter should be deterministic, local, cheap, and reproducible.
   - Add optional LLM-assisted correction later behind an explicit flag such as `--use-llm`, but do not implement it in the first version unless the repo already has an LLM client.

5. **Prefer local/offline processing.**
   - The conversion stage must work without network access.
   - Downloading PDFs from the web is a separate optional command.

---

## Recommended Tool Choices

Implement these as pluggable engines or adapters. Do not hard-code the whole pipeline around one library.

### Default engine: PyMuPDF + PyMuPDF4LLM

Use for fast local conversion, page inspection, rendering, metadata, page statistics, and common PDF-to-Markdown conversion.

Expected packages:

```bash
pip install pymupdf pymupdf4llm
```

Use cases:

- born-digital PDFs
- normal academic papers
- multi-column layouts
- basic tables
- page rendering
- extracting text blocks, words, images, metadata

### Optional advanced engine: Docling

Use when the document has complex layout, formulas, tables, or when structured JSON export is useful.

Expected package:

```bash
pip install docling
```

Implement as an optional backend. If import fails, the CLI should show a clear message instead of crashing.

### Optional advanced engine: Marker

Use for difficult scientific documents, formulas, tables, and image extraction. Marker can be strong, but it may be heavier and has licensing/commercial-use considerations. Keep it optional.

Expected package or CLI integration depends on the installed Marker distribution. Implement by subprocess only if a `marker_single` or equivalent CLI is available, or by Python API if already present in the environment.

### Optional scientific metadata/citation engine: GROBID

Use only for scientific papers when reference parsing, bibliography metadata, DOI extraction, or TEI XML is needed.

Implement as an optional HTTP client adapter:

```text
GROBID server URL from config or --grobid-url
```

Do not make GROBID mandatory for basic conversion.

### OCR engine: OCRmyPDF

Use for scanned PDFs or pages with little/no extractable text.

Expected external binaries:

```bash
ocrmypdf
# usually also needs tesseract and language packs
```

Behavior:

- `--ocr never`: never run OCR.
- `--ocr auto`: run OCR only if preflight detects scanned/image-heavy pages.
- `--ocr always`: run OCR before conversion.

If OCR is requested but `ocrmypdf` is missing, return a clear error with installation hints.

---

## CLI Requirements

Create a Python package named `pdf2md_agent` with a console command:

```bash
pdf2md-agent
```

### Command: inspect

```bash
pdf2md-agent inspect input.pdf --out out_dir
```

Outputs:

```text
out_dir/preflight.json
out_dir/pages/page_0001.png   # at least first page, plus suspicious pages
```

Preflight JSON must include:

```json
{
  "source_pdf": "input.pdf",
  "sha256": "...",
  "page_count": 12,
  "encrypted": false,
  "metadata": {},
  "pages": [
    {
      "page": 1,
      "width": 612,
      "height": 792,
      "word_count": 520,
      "char_count": 3100,
      "image_count": 2,
      "drawing_count": 18,
      "is_probably_scanned": false,
      "warnings": []
    }
  ],
  "document_warnings": []
}
```

### Command: convert

```bash
pdf2md-agent convert input.pdf --out out_dir --engine auto --ocr auto --render-pages --extract-assets --chunk
```

Arguments:

```text
--engine auto|pymupdf4llm|docling|marker|text
--ocr auto|never|always
--render-pages / --no-render-pages
--extract-assets / --no-extract-assets
--chunk / --no-chunk
--chunk-size 1200
--chunk-overlap 150
--strict
--keep-normalized-pdf
--config config.yaml
```

Outputs:

```text
out_dir/document.md
out_dir/document.json                 # if the chosen engine can produce it; otherwise minimal page/block JSON
out_dir/manifest.json
out_dir/pages/*.png                   # if --render-pages
out_dir/tables/*.csv                  # if table extraction succeeds
out_dir/tables/*.md
out_dir/figures/*                     # if image/figure extraction succeeds
out_dir/chunks/chunks.jsonl           # if --chunk
out_dir/logs/preflight.json
out_dir/logs/validation.json
```

### Command: batch

```bash
pdf2md-agent batch ./papers --out ./converted --engine auto --ocr auto --jobs 4
```

Behavior:

- Recursively find `*.pdf`.
- Create one output subdirectory per PDF using a safe slug.
- Never overwrite existing outputs unless `--overwrite` is passed.
- Write `batch_summary.json` with success/failure status.

---

## Markdown Format Requirements

`document.md` must contain explicit page anchors.

Recommended format:

```markdown
# <detected title or PDF filename>

<!-- source: paper.pdf -->
<!-- sha256: ... -->
<!-- engine: pymupdf4llm -->

<a id="page-1"></a>

## Page 1

... extracted text ...

![Figure p1-1](figures/page_0001_img_01.png)

Table p1-1: [CSV](tables/page_0001_table_01.csv)

| col1 | col2 |
|---|---|
| ... | ... |

<a id="page-2"></a>

## Page 2

...
```

Rules:

- Do not silently drop pages.
- If a page has no extractable text, include a page section anyway and add a warning comment:

```markdown
<!-- warning: no extractable text on this page; see pages/page_0004.png -->
```

- Remove obvious repeated headers/footers only when the converter is confident. Otherwise preserve them and mark them in validation warnings.
- Preserve equations as LaTeX if an engine supports it. If not, preserve the surrounding text and attach the rendered page image for fallback.
- Preserve tables as Markdown when possible and as CSV files always when table extraction succeeds.

---

## Manifest Requirements

`manifest.json` must be machine-readable and stable. Include at least:

```json
{
  "schema_version": "0.1.0",
  "source_pdf": "...",
  "source_sha256": "...",
  "created_at_utc": "...",
  "tool_version": "...",
  "engine": "pymupdf4llm",
  "ocr_mode": "auto",
  "normalized_pdf": null,
  "page_count": 12,
  "outputs": {
    "markdown": "document.md",
    "json": "document.json",
    "pages_dir": "pages",
    "figures_dir": "figures",
    "tables_dir": "tables",
    "chunks": "chunks/chunks.jsonl"
  },
  "page_stats": [
    {
      "page": 1,
      "char_count_preflight": 3100,
      "char_count_markdown": 2950,
      "word_count_preflight": 520,
      "is_probably_scanned": false,
      "warnings": []
    }
  ],
  "warnings": [],
  "validation": {
    "status": "pass",
    "checks": []
  }
}
```

---

## Preflight Implementation Details

Use PyMuPDF for preflight.

Pseudo-code:

```python
import hashlib
import fitz  # pymupdf


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inspect_pdf(path: str) -> dict:
    doc = fitz.open(path)
    result = {
        "source_pdf": str(path),
        "sha256": sha256_file(path),
        "page_count": doc.page_count,
        "encrypted": doc.needs_pass,
        "metadata": doc.metadata or {},
        "pages": [],
        "document_warnings": [],
    }

    for i, page in enumerate(doc, start=1):
        text = page.get_text("text") or ""
        words = page.get_text("words") or []
        images = page.get_images(full=True) or []
        drawings = page.get_drawings() or []

        # Heuristic only. Tune with tests.
        is_probably_scanned = len(words) < 20 and len(images) >= 1

        result["pages"].append({
            "page": i,
            "width": float(page.rect.width),
            "height": float(page.rect.height),
            "word_count": len(words),
            "char_count": len(text),
            "image_count": len(images),
            "drawing_count": len(drawings),
            "is_probably_scanned": is_probably_scanned,
            "warnings": [] if len(text.strip()) else ["no_text_extracted"],
        })
    return result
```

Also render suspicious pages:

- first page
- pages marked `is_probably_scanned`
- pages with `char_count == 0`
- pages with unusually low text compared to neighboring pages

Use `page.get_pixmap(dpi=200, alpha=False)` for rendering.

---

## OCR Normalization

When OCR is needed, run OCRmyPDF through subprocess:

```bash
ocrmypdf --skip-text --deskew --clean input.pdf normalized.pdf
```

Suggested behavior:

- Use `--skip-text` in auto mode so existing text pages are not unnecessarily re-OCRed.
- Add language support through config, for example `ocr_languages: eng+chi_sim`.
- Put the normalized PDF in `out_dir/logs/normalized.pdf` unless `--keep-normalized-pdf` is false.
- Record the exact OCR command in `manifest.json`.

Handle failures:

- If OCR fails, keep the original PDF conversion path but add a high-severity warning.
- In `--strict` mode, fail conversion if OCR was required but failed.

---

## Conversion Engine Interface

Create a protocol-like interface:

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ConversionResult:
    markdown: str
    document_json: dict[str, Any]
    engine: str
    warnings: list[str]


class ConversionEngine:
    name: str

    def is_available(self) -> bool:
        raise NotImplementedError

    def convert(self, pdf_path: Path, out_dir: Path, config: dict[str, Any]) -> ConversionResult:
        raise NotImplementedError
```

### `pymupdf4llm` engine

Use `pymupdf4llm.to_markdown()` for Markdown. Try to enable page chunks or page-aware output if the API supports it in the installed version. If page-aware output is not available, insert page anchors by converting page ranges one at a time.

Important: always preserve page boundaries.

Pseudo-code:

```python
import pymupdf4llm


def convert_with_pymupdf4llm(pdf_path, out_dir, config):
    # Prefer per-page conversion to guarantee page anchors.
    # If the installed pymupdf4llm supports pages=[...], use it.
    # Otherwise fall back to whole-document conversion and add best-effort anchors.
    md = pymupdf4llm.to_markdown(str(pdf_path))
    return ConversionResult(
        markdown=md,
        document_json={},
        engine="pymupdf4llm",
        warnings=[],
    )
```

### `docling` engine

Use Docling's `DocumentConverter` if installed. Export Markdown and JSON if available.

Pseudo-code:

```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert(str(pdf_path))
md = result.document.export_to_markdown()
# Also export JSON if the API supports it; otherwise serialize minimal structure.
```

### `marker` engine

Use a subprocess wrapper if a Marker CLI is available. Detect CLI by `shutil.which()`.

Do not make Marker required.

### `text` fallback engine

Use PyMuPDF's `page.get_text("text")` per page. This is lower quality but useful when higher-level engines fail. Add a warning:

```text
fallback_text_engine_used
```

---

## Asset Extraction

### Rendered page images

Always implement rendering using PyMuPDF.

```python
pix = page.get_pixmap(dpi=200, alpha=False)
pix.save(str(out_dir / "pages" / f"page_{page_no:04d}.png"))
```

### Tables

Use PyMuPDF `page.find_tables()` where available.

For each table:

- Save CSV: `tables/page_0001_table_01.csv`
- Save Markdown: `tables/page_0001_table_01.md`
- Add references to `document.md`
- Add table metadata to `document.json` and `manifest.json`

If table extraction fails, do not crash. Add warning.

### Figures/images

Use PyMuPDF image extraction and/or image bounding boxes.

For each extracted image:

- Save to `figures/page_0001_img_01.<ext>`
- Add relative link in Markdown if the engine does not already include it
- Record page number and bbox when available

For complex figures made of vector graphics, image extraction may fail. In that case, rely on full-page PNGs as a visual fallback and add a warning.

---

## Chunking Requirements

Create `chunks/chunks.jsonl`.

Each line:

```json
{
  "id": "<source_sha256>:p0001:c0001",
  "source_pdf": "paper.pdf",
  "source_sha256": "...",
  "page_start": 1,
  "page_end": 2,
  "text": "...",
  "markdown_path": "document.md",
  "anchors": ["page-1", "page-2"],
  "char_count": 1180,
  "token_estimate": 320
}
```

Chunking rules:

- Never merge unrelated sections just to hit target size.
- Prefer splitting by headings, then paragraphs, then sentences.
- Keep tables intact when possible.
- Preserve page span metadata.
- Default `chunk_size=1200` characters, `chunk_overlap=150` characters. Make configurable.

---

## Validation Requirements

Create `logs/validation.json` and embed summary in `manifest.json`.

Checks:

1. **Page count check**
   - Number of page anchors in Markdown should equal original PDF page count.

2. **Coverage check**
   - Compare preflight `char_count` with markdown chars per page.
   - Warn if a non-scanned page loses most text.
   - Suggested warning threshold: `markdown_chars < 0.5 * preflight_chars` for pages with `preflight_chars > 500`.

3. **Empty page check**
   - If a page has zero Markdown text and was not blank/scanned, warn.

4. **Asset link check**
   - Verify all local Markdown links to figures/tables exist.

5. **Chunk check**
   - Verify every chunk has source hash and page span.

6. **Strict mode**
   - If `--strict` is set, fail on high-severity warnings.

Validation output example:

```json
{
  "status": "warn",
  "checks": [
    {
      "name": "page_count",
      "status": "pass",
      "detail": "12 page anchors found for 12 pages"
    },
    {
      "name": "coverage",
      "status": "warn",
      "page": 7,
      "detail": "Markdown chars much lower than preflight chars"
    }
  ]
}
```

---

## Config File

Support YAML config:

```yaml
engine: auto
ocr: auto
ocr_languages: eng
render_pages: true
extract_assets: true
chunk: true
chunk_size: 1200
chunk_overlap: 150
strict: false
engines:
  prefer:
    - pymupdf4llm
    - docling
    - text
  marker_cli: marker_single
  grobid_url: http://localhost:8070
validation:
  coverage_ratio_warn: 0.5
  render_dpi: 200
```

CLI flags override config values.

---

## Suggested Repository Structure

```text
pdf2md-agent/
  pyproject.toml
  README.md
  src/
    pdf2md_agent/
      __init__.py
      cli.py
      config.py
      preflight.py
      ocr.py
      engines/
        __init__.py
        base.py
        pymupdf4llm_engine.py
        docling_engine.py
        marker_engine.py
        text_engine.py
      assets.py
      markdown.py
      chunking.py
      validation.py
      manifest.py
      utils.py
  tests/
    test_preflight.py
    test_chunking.py
    test_validation.py
    test_cli_smoke.py
  examples/
    config.yaml
```

---

## `pyproject.toml` Requirements

Use Python 3.10+.

Core dependencies:

```toml
[project]
name = "pdf2md-agent"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
  "pymupdf>=1.24",
  "pymupdf4llm",
  "typer>=0.12",
  "pydantic>=2",
  "pyyaml>=6",
  "rich>=13",
]

[project.optional-dependencies]
docling = ["docling"]
marker = []
grobid = ["httpx>=0.27"]
test = ["pytest", "reportlab"]

[project.scripts]
pdf2md-agent = "pdf2md_agent.cli:app"
```

Use Typer for the CLI.

---

## README Requirements

README must include:

1. Why PDF-to-Markdown needs validation.
2. Installation.
3. CLI examples.
4. Output directory explanation.
5. OCR setup notes.
6. Engine comparison:
   - PyMuPDF4LLM: default, fast, local.
   - Docling: advanced structured conversion.
   - Marker: optional, strong on scientific layouts but heavier/licensing considerations.
   - Text fallback: low fidelity, emergency fallback only.
7. How to use the output in an Agent/RAG workflow.
8. Known limitations:
   - PDF reading order is not guaranteed.
   - tables/equations/figures may need visual fallback.
   - OCR can make mistakes.
   - validation warns about likely problems; it cannot prove perfect extraction.

---

## Tests

Create tests that do not require internet.

### Unit tests

- `sha256_file()` stable output.
- chunking preserves page spans.
- validation catches missing page anchors.
- validation catches missing asset links.

### Synthetic PDF tests

Use `reportlab` in tests to generate small PDFs:

1. text-only one-page PDF
2. two-page PDF
3. PDF with a simple table-like layout
4. PDF with an embedded image if easy

Avoid requiring OCR in the default test suite. Add OCR tests behind a marker such as:

```bash
pytest -m ocr
```

### CLI smoke test

Generate a temporary PDF, run:

```bash
pdf2md-agent convert sample.pdf --out out --engine text --ocr never --render-pages --chunk
```

Assert these files exist:

- `document.md`
- `manifest.json`
- `logs/preflight.json`
- `logs/validation.json`
- `chunks/chunks.jsonl`

---

## Implementation Order

1. Create package skeleton and `pyproject.toml`.
2. Implement config loading and CLI.
3. Implement preflight and page rendering.
4. Implement text fallback engine.
5. Implement PyMuPDF4LLM engine.
6. Implement Markdown page-anchor normalization.
7. Implement manifest writing.
8. Implement validation.
9. Implement chunking.
10. Implement asset extraction for rendered pages and basic tables.
11. Add optional OCRmyPDF wrapper.
12. Add optional Docling engine.
13. Add optional Marker wrapper.
14. Add README and tests.

---

## Acceptance Criteria

The task is complete when all of the following are true:

1. `pdf2md-agent convert sample.pdf --out out --engine auto --ocr auto --render-pages --extract-assets --chunk` works on a normal born-digital PDF.
2. Output includes `document.md`, `manifest.json`, `logs/preflight.json`, `logs/validation.json`, page images, and chunks.
3. Markdown contains explicit page anchors for every page.
4. Chunks contain stable IDs, source hash, and page spans.
5. Validation detects at least these problems:
   - missing page anchors
   - missing asset links
   - empty Markdown page where preflight found text
6. Missing optional engines do not crash the default workflow.
7. OCR errors are reported clearly.
8. Unit tests and CLI smoke test pass.
9. README explains limitations honestly.

---

## Notes for Future Extensions

Do not implement these unless the core version is complete:

- Browser-assisted paper downloading.
- Chrome DevTools MCP workflow for web pages that block simple downloads.
- Zotero/Semantic Scholar/arXiv metadata enrichment.
- LLM-assisted table repair.
- LLM-assisted figure caption matching.
- Cross-paper literature review pipeline.
- Vector database ingestion.

Chrome DevTools MCP is useful for browser automation, screenshots, and debugging web interactions. It is not the core PDF parser. Keep downloading/acquisition separate from PDF conversion.

---

## Reference URLs for Implementation

Use these official/project references when checking APIs:

- PyMuPDF4LLM docs: https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/
- PyMuPDF Page API: https://pymupdf.readthedocs.io/en/latest/page.html
- PyMuPDF text/table recipes: https://pymupdf.readthedocs.io/en/latest/recipes-text.html
- Docling docs: https://docling-project.github.io/docling/
- Marker project: https://github.com/datalab-to/marker
- OCRmyPDF docs: https://ocrmypdf.readthedocs.io/en/latest/
- GROBID docs: https://grobid.readthedocs.io/en/latest/Introduction/
- Microsoft MarkItDown: https://github.com/microsoft/markitdown
- Chrome DevTools MCP: https://developer.chrome.com/docs/devtools/agents
