# pdf2md-agent

<p align="center">
  <strong>Local, traceable PDF ingestion for GPT research workflows, AI agents, and RAG pipelines.</strong>
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.zh-CN.md">中文</a>
</p>

<p align="center">
  <a href="https://github.com/BoyangGuo1789/pdf2md-agent/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/BoyangGuo1789/pdf2md-agent/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-green.svg"></a>
</p>

Most research agents start with PDFs. The problem is that a PDF is not the document a language model wants to read.

PDFs are page layouts, not stable research context. A paper may contain columns, headers, footers, equations, tables, captions, references, scanned regions, and positioned text. When that layout is flattened by a single converter, important context can disappear silently while the downstream GPT workflow still produces confident answers.

`pdf2md-agent` turns that fragile first step into an auditable ingestion layer. It creates Markdown for the model to read, JSON for structured inspection, rendered page images for visual fallback, extracted assets for review, retrieval chunks for RAG, and manifests/logs that make conversion risk visible.

Use it before asking GPT to summarize papers, compare related work, extract claims, build literature maps, or index PDFs into a retrieval system. The output is not just a `.md` file; it is a research bundle that agents can read, retrieve, cite, and humans can audit.

## Why GPT Research Needs This Step

| GPT research need | Why raw PDFs are not enough |
| --- | --- |
| Stable text | PDFs store visual layout, not clean reading-order text |
| Reliable retrieval | RAG needs chunks with stable IDs, source hashes, and page spans |
| Agent workflows | Agents need intermediate artifacts they can inspect, cite, and revisit |
| Debuggable answers | Humans need to see whether an error came from parsing or reasoning |
| Long-term reuse | Research pipelines should not re-parse the same PDF differently every time |

## What You Get

| Output | Purpose |
| --- | --- |
| `document.md` | Markdown formatted for LLM reading and downstream review |
| `document.json` | Structured extraction output for programmatic inspection |
| `manifest.json` | Bundle metadata, source hash, engine, warnings, and validation status |
| `pages/page_*.png` | Visual fallback when text extraction is uncertain |
| `figures/` and `tables/` | Extracted assets for review and reuse when available |
| `chunks/chunks.jsonl` | Retrieval-ready chunks for RAG and agent pipelines |
| `logs/` | Preflight and validation details so ingestion risk is not hidden |

## Different From Ordinary PDF-to-Markdown

| Ordinary converter | `pdf2md-agent` |
| --- | --- |
| Optimizes for one Markdown file | Optimizes for an auditable AI research bundle |
| May hide page-order and extraction failures | Writes manifests, warnings, validation logs, and page renders |
| Often loses citation context | Keeps page anchors, page spans, and source hashes |
| Requires separate RAG preprocessing | Can emit retrieval-ready JSONL chunks |
| Treats Markdown as the final truth | Treats Markdown as the readable layer, backed by structured and visual evidence |

## Quick Start

Use Python 3.10 or newer.

```bash
git clone https://github.com/BoyangGuo1789/pdf2md-agent.git
cd pdf2md-agent
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Inspect a PDF before conversion:

```bash
pdf2md-agent inspect paper.pdf --out inspect_out
```

Convert a PDF into a research bundle:

```bash
pdf2md-agent convert paper.pdf \
  --out converted/paper \
  --engine auto \
  --ocr auto \
  --render-pages \
  --extract-assets \
  --chunk
```

## Design Principle

The core idea is simple:

> Markdown is for the model to read, but it is not the only source of truth.

Ordinary PDF-to-Markdown tools usually ask one question:

```text
Can we extract the text from this PDF?
```

`pdf2md-agent` asks a stricter question:

```text
Can the extracted material be used by AI agents in a stable, traceable, and reviewable way?
```

That changes the output shape. Each page should remain addressable. Chunks should carry page spans and source hashes. Tables and figures should become separate assets when possible. Suspicious pages should be renderable for visual review. Conversion should leave a manifest and validation report so failure modes are visible instead of hidden.

## Output Bundle

Each conversion writes a directory that keeps the readable text, structured metadata, rendered pages, extracted assets, chunks, and validation evidence together.

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

Use `document.md` for LLM reading and citation-aware prompting. Use `chunks/chunks.jsonl` for vector indexing. Use `pages/page_*.png` when text extraction quality needs visual verification.

## Command Reference

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

Run with a config file:

```bash
pdf2md-agent convert paper.pdf --out converted/paper --config examples/config.yaml
```

CLI flags override config file values.

## Engines

| Engine | Role | Notes |
| --- | --- | --- |
| `pymupdf4llm` | Default preferred engine | Fast, local, suitable for born-digital PDFs |
| `docling` | Optional structured conversion | Useful for complex layouts when installed |
| `marker` | Optional CLI wrapper | Useful for difficult scientific layouts |
| `text` | Low-fidelity fallback | Preserves page boundaries with plain PyMuPDF text extraction |

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

## Development

Install test dependencies:

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
