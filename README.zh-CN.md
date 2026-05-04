# pdf2md-agent

[English](README.md) | [中文](README.zh-CN.md)

`pdf2md-agent` 是一个本地 PDF-to-Markdown 摄取管线，面向 AI Agent、研究助手、文献综述和 RAG 检索增强生成场景。

它不是又一个简单的“PDF 转文本”工具。它真正想做的是：把复杂 PDF 变成 AI Agent 可以可靠阅读、引用、复查、切块和复用的研究上下文。

很多 AI 研究工作流的第一步，是把 PDF 直接丢给模型或 Agent。这个做法看起来方便，但实际很不稳定。PDF 本质上不是为机器理解设计的结构化文本文件，而更像是一组页面绘制指令。一份 PDF 里可能同时包含多栏排版、页眉页脚、脚注、公式、图表、表格、参考文献、扫描页、嵌入图片和复杂阅读顺序。不同解析器面对同一份 PDF，可能会给出不同的文本顺序，也可能悄悄漏掉重要内容。

这会导致几个实际问题：

- 关键段落、公式、图注或表格内容可能丢失；
- 多栏论文可能被按错误顺序读取；
- 标题、段落、列表、表格和引用关系可能被打散；
- 模型回答时无法追溯到原文页码；
- 出错后很难判断是 PDF 解析错了，还是模型理解错了；
- 每个下游任务都重新解析同一份 PDF，结果不稳定，成本也更高。

AI auto-research 的瓶颈不只是“模型会不会总结论文”，更是“模型读到的材料本身是否足够完整、可追溯、可复查”。

它不会只相信单个 PDF 解析器的结果，而是把 PDF 转成一个可追踪、可验证的研究资料包：

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

## 为什么需要它

PDF 转 Markdown 天然有信息损失。阅读顺序、表格、公式、图片、扫描页都可能悄悄出错。`pdf2md-agent` 默认生成适合 LLM 阅读的 Markdown，同时保留来源哈希、页码锚点、页面图片、结构化 JSON、表格、图像资产、chunks 和验证日志，让下游 Agent 可以回溯证据页并识别高风险转换结果。

它的核心设计可以概括为：

> Markdown 是给模型读的，但不是唯一真相。

`document.md`、`document.json`、页面图片、表格文件、图像资产、chunks、manifest 和 validation logs 共同构成一个 research bundle。这个资料包可以直接用于论文总结、文献综述、多篇论文对比、带引用问答、RAG 入库、多模态核验和知识库构建。

普通 PDF 转 Markdown 工具通常问的是：

```text
能不能把 PDF 里的文字提出来？
```

`pdf2md-agent` 问的是一个更严格的问题：

```text
提取出来的内容，能不能被 AI Agent 长期、稳定、可追溯地使用？
```

这会影响整个设计。每一页都应该可定位，每个 chunk 都应该带来源哈希和页码范围，表格和图片应该尽可能被单独保存，可疑页面应该渲染成图片供复查，每次转换都应该留下 manifest 和 validation report，让问题暴露出来，而不是被隐藏在一次性文本抽取结果里。

整体管线是：

```text
预检 -> 可选 OCR 归一化 -> 布局感知转换 -> 资产提取 -> 切块 -> 验证 -> 输出资料包
```

## 功能

- 生成带页码锚点的 `document.md`，每一页都可追踪。
- 生成 `manifest.json`，记录来源哈希、转换引擎、页面统计、输出文件、警告和验证状态。
- 渲染每页 PNG，用于视觉核验和多模态兜底。
- 在 PyMuPDF 可识别时提取图片和基础表格。
- 生成适合检索入库的 `chunks/chunks.jsonl`，包含稳定 ID、来源哈希和页码范围。
- 默认本地确定性处理，不调用 LLM。
- 可选支持 Docling 和 Marker 引擎。
- 可选通过 OCRmyPDF 处理扫描 PDF。

## 安装

需要 Python 3.10 或更高版本。

```bash
git clone https://github.com/BoyangGuo1789/pdf2md-agent.git
cd pdf2md-agent
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

如果只作为运行工具使用：

```bash
python -m pip install -e .
```

## 快速开始

先预检一个 PDF：

```bash
pdf2md-agent inspect paper.pdf --out inspect_out
```

转换单个普通 PDF：

```bash
pdf2md-agent convert paper.pdf --out converted/paper --engine auto --ocr auto --render-pages --extract-assets --chunk
```

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

## 输出说明

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

## 转换引擎

- `pymupdf4llm`：默认优先引擎，速度快、本地运行，适合普通 born-digital PDF。
- `docling`：可选结构化转换引擎，适合复杂版面。
- `marker`：可选 CLI 包装器，适合较难的科学文档版面。
- `text`：低保真 PyMuPDF 纯文本兜底，会保留页边界。

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

```bash
pdf2md-agent convert paper.pdf --out converted/paper --config examples/config.yaml
```

命令行参数会覆盖配置文件中的对应值。

## 开发

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
