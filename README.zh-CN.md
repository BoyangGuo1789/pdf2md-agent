# pdf2md-agent

<p align="center">
  <strong>面向 AI Agent、研究助手和 RAG 管线的可追溯 PDF-to-Markdown 摄取工具。</strong>
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.zh-CN.md">中文</a>
</p>

<p align="center">
  <a href="https://github.com/BoyangGuo1789/pdf2md-agent/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/BoyangGuo1789/pdf2md-agent/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-green.svg"></a>
</p>

`pdf2md-agent` 会把复杂 PDF 转成可审计的研究资料包：给 LLM 阅读的 Markdown、给程序检查的 JSON、用于视觉兜底的页面图片、用于检索入库的 chunks，以及能暴露转换风险的日志。

PDF 不是干净的结构化文本文件，更像是一组页面绘制指令。一篇论文里可能同时包含多栏排版、页眉页脚、脚注、公式、图表、表格、参考文献、扫描页、嵌入图片和复杂阅读顺序。如果 Agent 只读取某一个解析器吐出的文本，关键上下文可能会悄悄消失。

这个项目的目标更严格：**让提取出来的研究材料足够稳定、可追溯、可复查，能够支撑后续 AI 工作流。**

## 一眼看懂

| 需求 | `pdf2md-agent` 提供什么 |
| --- | --- |
| 给 LLM 阅读 | 带页码锚点的 `document.md` |
| 保留来源证据 | `manifest.json` 记录来源哈希、引擎、输出文件、警告和验证状态 |
| 视觉兜底 | 渲染 `pages/page_*.png`，用于版面敏感内容复查 |
| RAG 入库 | `chunks/chunks.jsonl` 包含稳定 ID、页码范围和来源哈希 |
| 资产复用 | 在可识别时提取图片和基础表格 |
| 本地处理 | 默认确定性转换，不调用 LLM |

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

## 为什么需要它

很多 AI 研究工作流的第一步，是把 PDF 直接丢给模型或 Agent。这个做法看起来方便，但实际很不稳定。不同解析器面对同一份文件，可能会给出不同文本顺序，漏掉表格内容，丢失图注，打平公式，或者无法保留带引用问答所需要的页级证据。

这会导致几个实际问题：

- 关键段落、公式、图注或表格内容可能丢失；
- 多栏论文可能被按错误顺序读取；
- 标题、段落、列表、表格和引用关系可能被打散；
- 模型回答时无法追溯到原文页码；
- 出错后很难判断是 PDF 解析错了，还是模型理解错了；
- 下游任务可能重复解析同一份 PDF，结果不稳定。

AI auto-research 的瓶颈不只是“模型会不会总结论文”，更是“模型读到的材料本身是否足够完整、可追溯、可复查”。

它的核心设计可以概括为：

> Markdown 是给模型读的，但不是唯一真相。

普通 PDF 转 Markdown 工具通常问的是：

```text
能不能把 PDF 里的文字提出来？
```

`pdf2md-agent` 问的是一个更严格的问题：

```text
提取出来的内容，能不能被 AI Agent 长期、稳定、可追溯地使用？
```

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
