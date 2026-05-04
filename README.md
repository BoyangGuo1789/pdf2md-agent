# pdf2md-agent

<p align="center">
  <strong>Traceable PDF-to-Markdown ingestion for AI agents, research assistants, and RAG pipelines.</strong>
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.zh-CN.md">中文</a>
</p>

<p align="center">
  <a href="https://github.com/BoyangGuo1789/pdf2md-agent/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/BoyangGuo1789/pdf2md-agent/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-green.svg"></a>
</p>

`pdf2md-agent` turns messy PDFs into auditable research bundles: Markdown for LLM reading, JSON for structured inspection, page images for visual fallback, chunks for retrieval, and logs that make conversion risk visible.

PDFs are not clean text documents. They are closer to page drawing instructions, and a single paper may mix multi-column layouts, headers, footers, footnotes, equations, charts, tables, references, scanned pages, embedded images, and ambiguous reading order. If an agent reads only one parser's text output, important context can disappear silently.

This project is built around a stricter target: **make extracted research material stable enough, traceable enough, and inspectable enough for downstream AI workflows.**

## At a Glance

| Need | What `pdf2md-agent` provides |
| --- | --- |
| LLM-readable text | Page-aware `document.md` with explicit anchors |
| Reliable provenance | `manifest.json` with source hash, engine, outputs, warnings, and validation status |
| Visual fallback | Rendered `pages/page_*.png` for layout-sensitive review |
| RAG ingestion | `chunks/chunks.jsonl` with stable IDs, page spans, and source hashes |
| Asset reuse | Extracted figures and basic tables when available |
| Local processing | Deterministic conversion by default; no LLM calls are made |

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

## Why This Exists

Many AI research workflows start by handing a PDF directly to a model or agent. That is convenient, but unstable. Different parsers can extract the same file in different orders, drop table content, miss captions, flatten formulas, or lose the page-level evidence needed for citation-aware answers.

That creates practical failures:

- important paragraphs, formulas, captions, or table content can be dropped;
- multi-column papers can be read in the wrong order;
- headings, paragraphs, lists, tables, and citations can lose structure;
- model answers cannot be traced back to source pages;
- mistakes are hard to debug because it is unclear whether the parser or the model failed;
- downstream tasks may re-parse the same PDF differently.

The bottleneck in AI auto-research is not only whether the model can summarize a paper. It is whether the material given to the model is complete, traceable, and reviewable enough to support reliable downstream work.

The core design principle is:

> Markdown is for the model to read, but it is not the only source of truth.

Ordinary PDF-to-Markdown tools usually ask:

```text
Can we extract the text from this PDF?
```

`pdf2md-agent` asks a stricter question:

```text
Can the extracted material be used by AI agents in a stable, traceable, and reviewable way?
```

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
