# pdf2md-agent

[English](README.md) | [中文](README.zh-CN.md)

`pdf2md-agent` is a local PDF-to-Markdown ingestion pipeline for AI agents, research assistants, literature review workflows, and retrieval-augmented generation.

It is not meant to be just another "PDF to text" converter. Its purpose is to turn messy PDFs into reliable research context that agents can read, cite, inspect, chunk, and reuse.

Many AI research workflows start by handing a PDF directly to a model or an agent. That is convenient, but unstable. PDFs are not structured text documents; they are closer to page drawing instructions. A single file may contain multi-column layouts, headers, footers, footnotes, formulas, charts, tables, references, scanned pages, embedded images, and ambiguous reading order. Different parsers can extract the same PDF in different orders or silently miss important content.

That causes practical failures:

- important paragraphs, formulas, captions, or table content can be dropped;
- multi-column papers can be read in the wrong order;
- headings, paragraphs, lists, tables, and citations can lose structure;
- model answers cannot be traced back to source pages;
- mistakes are hard to debug because it is unclear whether the parser or the model failed;
- every downstream task may re-parse the same PDF differently.

The bottleneck in AI auto-research is not only whether the model can summarize a paper. It is whether the material given to the model is complete enough, traceable enough, and inspectable enough to support reliable downstream work.

It converts a PDF into a traceable research bundle instead of trusting a single parser output:

```text
out_dir/
  document.md
  document.json
  manifest.json
  pages/
    page_0001.png
  figures/
  tables/
  chunks/
    chunks.jsonl
  logs/
    preflight.json
    validation.json
```

## Why

PDF-to-Markdown conversion is lossy. Reading order, tables, equations, figures, and scanned pages can fail silently. `pdf2md-agent` keeps Markdown as the default LLM-readable output, while preserving provenance, visual fallbacks, structured assets, and validation signals so downstream agents can cite source pages and detect risky conversions.

The key idea is:

> Markdown is for the model to read, but it is not the only source of truth.

`document.md`, `document.json`, page images, table files, figure assets, chunks, manifests, and validation logs together form a research bundle. This bundle can be used for summarization, literature review, paper comparison, citation-aware Q&A, RAG indexing, multimodal verification, and knowledge-base construction.

Ordinary PDF-to-Markdown tools usually ask:

```text
Can we extract the text from this PDF?
```

`pdf2md-agent` asks a stricter question:

```text
Can the extracted material be used by AI agents in a stable, traceable, and reviewable way?
```

That changes the design. Each page should remain addressable. Chunks should carry source hashes and page spans. Tables and figures should become separate assets when possible. Suspicious pages should be rendered for visual review. Conversion should leave a manifest and validation report so failures are visible instead of hidden.

The pipeline is:

```text
preflight -> optional OCR normalization -> layout-aware conversion -> asset extraction -> chunking -> validation -> bundle output
```

## Features

- Page-aware `document.md` with explicit anchors for every page.
- `manifest.json` with source hash, engine, page stats, outputs, warnings, and validation status.
- Rendered page PNGs for visual verification and multimodal fallback.
- Extracted figures and basic tables when PyMuPDF can detect them.
- Retrieval-ready `chunks/chunks.jsonl` with stable IDs, source hashes, and page spans.
- Local deterministic conversion by default; no LLM calls are made.
- Optional engine adapters for Docling and Marker.
- Optional OCR normalization through OCRmyPDF.

## Installation

Use Python 3.10 or newer.

```bash
git clone https://github.com/BoyangGuo1789/pdf2md-agent.git
cd pdf2md-agent
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

For runtime-only usage:

```bash
python -m pip install -e .
```

## Quick Start

Inspect a PDF before conversion:

```bash
pdf2md-agent inspect paper.pdf --out inspect_out
```

Convert a single born-digital PDF:

```bash
pdf2md-agent convert paper.pdf --out converted/paper --engine auto --ocr auto --render-pages --extract-assets --chunk
```

Use the deterministic low-fidelity text fallback:

```bash
pdf2md-agent convert paper.pdf --out converted/paper-text --engine text --ocr never
```

Batch convert a folder:

```bash
pdf2md-agent batch ./papers --out ./converted --engine auto --ocr auto
```

Print default configuration:

```bash
pdf2md-agent config-defaults
```

## Output Details

`document.md` includes explicit page anchors:

```markdown
<a id="page-1"></a>

## Page 1
```

Each chunk in `chunks/chunks.jsonl` includes:

- `id`
- `source_pdf`
- `source_sha256`
- `page_start`
- `page_end`
- `text`
- `markdown_path`
- `anchors`
- `char_count`
- `token_estimate`

Use `document.md` for LLM reading and citation-aware prompting. Use `chunks/chunks.jsonl` for vector indexing. Use `pages/page_*.png` when the text extraction quality needs visual verification.

## Engines

- `pymupdf4llm`: default preferred engine. Fast, local, and suitable for born-digital PDFs.
- `docling`: optional structured conversion engine for complex layouts.
- `marker`: optional CLI-based wrapper for difficult scientific layouts.
- `text`: low-fidelity PyMuPDF fallback that preserves page boundaries.

Missing optional engines do not break the default workflow.

## OCR

OCR is optional and handled by the external `ocrmypdf` binary.

```bash
ocrmypdf --version
```

If `--ocr auto` detects scanned pages but OCRmyPDF is missing, conversion continues with a warning unless `--strict` is set. If `--ocr always` is used and OCRmyPDF is missing, the command fails with a clear error.

Example config:

```yaml
ocr: auto
ocr_languages: eng+chi_sim
```

## Configuration

See [examples/config.yaml](examples/config.yaml).

```bash
pdf2md-agent convert paper.pdf --out converted/paper --config examples/config.yaml
```

CLI flags override config file values.

## Development

```bash
python -m pip install -e ".[test]"
pytest
```

Run a manual smoke test:

```bash
pdf2md-agent convert sample.pdf --out out --engine text --ocr never --render-pages --chunk
```

## Known Limitations

- PDF reading order is not guaranteed.
- Tables, equations, and figures may require visual fallback.
- OCR can introduce recognition errors.
- Validation detects likely problems; it cannot prove perfect extraction.
- Batch conversion currently runs sequentially. `--jobs` is accepted for CLI compatibility and reserved for future parallel execution.

## License

MIT. See [LICENSE](LICENSE).
