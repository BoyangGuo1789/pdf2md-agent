# Requirements and Release Notes

[English](#english) | [中文](#中文)

## English

This document lists what is needed to run, test, and publish `pdf2md-agent`.

### Runtime Requirements

- Python 3.10 or newer.
- Core Python packages installed from `pyproject.toml`:
  - `pymupdf`
  - `pymupdf4llm`
  - `typer`
  - `pydantic`
  - `pyyaml`
  - `rich`

Install runtime dependencies:

```bash
python -m pip install -e .
```

Install test dependencies:

```bash
python -m pip install -e ".[test]"
```

### Optional Tools

- OCR: `ocrmypdf` plus Tesseract and language packs.
- Advanced structured conversion: `docling`.
- Marker conversion: a compatible Marker CLI such as `marker_single`.
- GROBID integration is reserved for future metadata work and is not required by the core workflow.

### Expected CLI Commands

```bash
pdf2md-agent inspect paper.pdf --out inspect_out
pdf2md-agent convert paper.pdf --out converted/paper --engine auto --ocr auto --render-pages --extract-assets --chunk
pdf2md-agent batch ./papers --out ./converted --engine auto --ocr auto
```

### Verification Before Release

Run:

```bash
pytest
pdf2md-agent --help
```

Recommended manual smoke test:

```bash
pdf2md-agent convert sample.pdf --out out --engine text --ocr never --render-pages --chunk
```

Required output files:

- `document.md`
- `document.json`
- `manifest.json`
- `logs/preflight.json`
- `logs/validation.json`
- `chunks/chunks.jsonl`
- `pages/page_0001.png`

### GitHub Release Checklist

- `README.md` is the default English landing page.
- `README.zh-CN.md` provides the Chinese landing page.
- `LICENSE` is present.
- `.gitignore` excludes virtual environments, caches, and generated outputs.
- GitHub Actions runs tests on supported Python versions.
- The repository should be public if the goal is open-source release.

## 中文

本文档列出运行、测试和开源发布 `pdf2md-agent` 所需要的东西。

### 运行环境

- Python 3.10 或更高版本。
- `pyproject.toml` 中定义的核心 Python 依赖：
  - `pymupdf`
  - `pymupdf4llm`
  - `typer`
  - `pydantic`
  - `pyyaml`
  - `rich`

安装运行依赖：

```bash
python -m pip install -e .
```

安装测试依赖：

```bash
python -m pip install -e ".[test]"
```

### 可选工具

- OCR：`ocrmypdf`，以及 Tesseract 和对应语言包。
- 高级结构化转换：`docling`。
- Marker 转换：兼容的 Marker CLI，例如 `marker_single`。
- GROBID 集成保留给未来元数据解析功能，核心流程不依赖它。

### 常用命令

```bash
pdf2md-agent inspect paper.pdf --out inspect_out
pdf2md-agent convert paper.pdf --out converted/paper --engine auto --ocr auto --render-pages --extract-assets --chunk
pdf2md-agent batch ./papers --out ./converted --engine auto --ocr auto
```

### 发布前验证

运行：

```bash
pytest
pdf2md-agent --help
```

建议手动 smoke test：

```bash
pdf2md-agent convert sample.pdf --out out --engine text --ocr never --render-pages --chunk
```

必须生成的输出文件：

- `document.md`
- `document.json`
- `manifest.json`
- `logs/preflight.json`
- `logs/validation.json`
- `chunks/chunks.jsonl`
- `pages/page_0001.png`

### GitHub 发布检查清单

- `README.md` 是默认英文介绍页。
- `README.zh-CN.md` 是中文介绍页。
- 已包含 `LICENSE`。
- `.gitignore` 已排除虚拟环境、缓存和生成输出。
- GitHub Actions 会在支持的 Python 版本上运行测试。
- 如果目标是开源发布，GitHub 仓库应设为 public。
