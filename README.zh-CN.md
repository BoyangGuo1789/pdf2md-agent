# pdf2md-agent

<p align="center">
  <strong>面向 GPT 研究流程、AI Agent 和 RAG 管线的本地、可追踪 PDF 摄取层。</strong>
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.zh-CN.md">中文</a>
</p>

<p align="center">
  <a href="https://github.com/BoyangGuo1789/pdf2md-agent/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/BoyangGuo1789/pdf2md-agent/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-green.svg"></a>
</p>

大多数研究 Agent 都从 PDF 开始。问题是，PDF 并不是语言模型真正想读取的文档格式。

PDF 是页面布局，不是稳定的研究上下文。一篇论文里可能有分栏、页眉页脚、公式、表格、图注、参考文献、扫描区域和带坐标的文字。当单一转换器把这些页面压平成文本时，关键信息可能会悄悄丢失，而后面的 GPT 工作流仍然会给出看起来很自信的回答。

`pdf2md-agent` 的价值，是把这个脆弱的第一步变成本地、可审计的摄取层。它生成给模型阅读的 Markdown、用于结构化检查的 JSON、作为视觉兜底的页面图片、便于复查的抽取资产、面向 RAG 的检索 chunks，以及能暴露转换风险的 manifest 和日志。

在让 GPT 总结论文、比较相关工作、抽取论点、构建文献图谱，或把 PDF 放进检索系统之前，可以先用它把 PDF 变成研究资料包。输出不只是一个 `.md` 文件，而是一组 Agent 可以阅读、检索、引用，人也可以复查的证据材料。

## 为什么 GPT 研究需要这一步

| GPT 研究需求 | 为什么原始 PDF 不够 |
| --- | --- |
| 稳定文本 | PDF 保存的是视觉版面，不是干净的阅读顺序文本 |
| 可靠检索 | RAG 需要带稳定 ID、来源哈希和页码范围的 chunks |
| Agent 工作流 | Agent 需要可以检查、引用和回溯的中间产物 |
| 可调试答案 | 人需要判断错误来自 PDF 解析，还是来自模型推理 |
| 长期复用 | 研究管线不应该每次都用不同方式重新解析同一份 PDF |

## 你会得到什么

| 输出 | 作用 |
| --- | --- |
| `document.md` | 适合 LLM 阅读和人工复查的 Markdown |
| `document.json` | 用于程序化检查的结构化抽取结果 |
| `manifest.json` | 资料包元数据、来源哈希、引擎、警告和验证状态 |
| `pages/page_*.png` | 当文本抽取不确定时提供视觉兜底 |
| `figures/` 和 `tables/` | 在可识别时提取图片和表格，便于复查和复用 |
| `chunks/chunks.jsonl` | 面向 RAG 和 Agent 管线的检索分块 |
| `logs/` | 记录预检和验证细节，让摄取风险可见 |

## 与普通 PDF-to-Markdown 工具的区别

| 普通转换器 | `pdf2md-agent` |
| --- | --- |
| 优化单个 Markdown 文件 | 优化可审计的 AI 研究资料包 |
| 可能隐藏阅读顺序和抽取错误 | 写出 manifest、警告、验证日志和页面渲染图 |
| 容易丢失引用上下文 | 保留页码锚点、页码范围和来源哈希 |
| 需要额外做 RAG 预处理 | 可以直接输出检索用 JSONL chunks |
| 把 Markdown 当成最终结果 | 把 Markdown 当成可读层，背后还有结构化和视觉证据 |

## 快速开始

需要 Python 3.10 或更高版本。

```bash
git clone https://github.com/BoyangGuo1789/pdf2md-agent.git
cd pdf2md-agent
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

先预检一个 PDF：

```bash
pdf2md-agent inspect paper.pdf --out inspect_out
```

把 PDF 转成研究资料包：

```bash
pdf2md-agent convert paper.pdf \
  --out converted/paper \
  --engine auto \
  --ocr auto \
  --render-pages \
  --extract-assets \
  --chunk
```

## 设计原则

核心想法很简单：

> Markdown 是给模型读的，但不是唯一真相。

普通 PDF 转 Markdown 工具通常只问一个问题：

```text
能不能把 PDF 里的文字提出来？
```

`pdf2md-agent` 问的是一个更严格的问题：

```text
提取出来的内容，能不能被 AI Agent 长期、稳定、可追溯地使用？
```

这个问题会改变输出形态。每一页都应该可定位，每个 chunk 都应该带页码范围和来源哈希，表格和图片应该尽可能被单独保存，可疑页面应该能渲染出来供视觉复查，每次转换都应该留下 manifest 和 validation report，让失败模式暴露出来，而不是隐藏在一次性文本抽取结果里。

## 输出资料包

每次转换都会写出一个目录，把可读文本、结构化元数据、页面渲染图、提取资产、chunks 和验证证据放在一起。

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

`document.md` 中会包含明确的页码锚点：

```markdown
<a id="page-1"></a>

## Page 1
```

`chunks/chunks.jsonl` 中每个 chunk 包含：

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

可以把 `document.md` 用于 LLM 阅读和带引用问答，把 `chunks/chunks.jsonl` 用于向量索引，把 `pages/page_*.png` 用于核验图表、公式、扫描页或版面敏感内容。

## 常用命令

使用低保真的纯文本兜底引擎：

```bash
pdf2md-agent convert paper.pdf --out converted/paper-text --engine text --ocr never
```

批量转换文件夹：

```bash
pdf2md-agent batch ./papers --out ./converted --engine auto --ocr auto
```

查看默认配置：

```bash
pdf2md-agent config-defaults
```

使用配置文件：

```bash
pdf2md-agent convert paper.pdf --out converted/paper --config examples/config.yaml
```

命令行参数会覆盖配置文件中的对应值。

## 转换引擎

| 引擎 | 作用 | 说明 |
| --- | --- | --- |
| `pymupdf4llm` | 默认优先引擎 | 速度快、本地运行，适合普通 born-digital PDF |
| `docling` | 可选结构化转换 | 安装后可用于复杂版面 |
| `marker` | 可选 CLI 包装器 | 可用于较难的科学文档版面 |
| `text` | 低保真兜底 | 用 PyMuPDF 提取纯文本并保留页边界 |

缺少可选引擎不会影响默认工作流。

## OCR

OCR 是可选功能，通过外部 `ocrmypdf` 命令处理。

```bash
ocrmypdf --version
```

如果 `--ocr auto` 检测到扫描页但系统没有安装 OCRmyPDF，工具会继续转换并记录警告，除非启用 `--strict`。如果使用 `--ocr always` 且 OCRmyPDF 缺失，命令会直接失败并给出清晰错误。

配置示例：

```yaml
ocr: auto
ocr_languages: eng+chi_sim
```

## 配置

参考 [examples/config.yaml](examples/config.yaml)。

## 开发

安装测试依赖：

```bash
python -m pip install -e ".[test]"
pytest
```

手动 smoke test：

```bash
pdf2md-agent convert sample.pdf --out out --engine text --ocr never --render-pages --chunk
```

## 已知限制

- PDF 的阅读顺序无法保证完全正确。
- 表格、公式和图片可能需要页面 PNG 作为视觉兜底。
- OCR 可能产生识别错误。
- 验证只能发现可能的问题，不能证明转换百分百完美。
- 批量转换当前是顺序执行。`--jobs` 已保留为未来并行执行接口。

## 许可证

MIT。详见 [LICENSE](LICENSE)。
