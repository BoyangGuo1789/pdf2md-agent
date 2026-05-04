# PDF2MD-Agent：让 AI Auto Research 先读懂文档

> 一个面向 AI Agent、RAG、论文阅读和自动化研究的文档解析基础设施。它把 PDF 转换成可读、可追溯、可校验的 Markdown 研究包，而不是让模型盲目读取一份复杂的 PDF。

---

## 1. 一句话介绍

**PDF2MD-Agent 是一个可复用的本地文档转换工具，它可以把论文、报告、技术文档等 PDF 转换成适合大语言模型和 Agent 使用的研究材料包，包括 Markdown、结构化 JSON、页面图片、表格、图像资产、检索 chunks 和校验报告。**

它的目标不是简单地“把 PDF 变成文本”，而是为 AI Auto Research 建立一个更可靠的文档入口。

---

## 2. 为什么需要这个项目？

很多人在使用大语言模型做论文阅读、文献综述、RAG 问答或者 Agent 自动研究时，第一步通常是：

```text
把 PDF 丢给模型 / Agent，让它直接读。
```

这个做法看起来方便，但实际上非常不稳定。

PDF 本质上不是为机器理解设计的“结构化文本文件”，而更像是一组页面绘制指令。一个 PDF 里可能包含多栏排版、页眉页脚、脚注、公式、图表、表格、参考文献、图片、扫描页和复杂的阅读顺序。不同解析器拿到同一份 PDF，可能会给出完全不同的文本顺序和结构。

这会导致几个常见问题：

- **内容缺失**：图表、表格、脚注、公式附近的文字可能被漏掉。
- **顺序错误**：多栏论文经常被解析成错误的阅读顺序。
- **结构丢失**：标题、段落、列表、表格和引用关系被打散。
- **无法追溯**：模型回答时不知道某句话来自原文哪一页。
- **难以复查**：一旦 Agent 总结错了，很难定位是模型错了，还是 PDF 解析阶段就错了。
- **难以复用**：每个下游任务都重新解析 PDF，结果不稳定，成本也高。

所以，AI Auto Research 的真正难点之一，不只是“模型会不会总结论文”，而是：

> **模型读到的材料本身是否完整、准确、可追溯、可复查。**

PDF2MD-Agent 正是为了解决这个问题。

---

## 3. 这个项目到底做什么？

PDF2MD-Agent 会把一份 PDF 转换成一个面向 AI 研究工作流的标准化输出目录。

输入：

```text
paper.pdf
```

输出：

```text
output_dir/
  document.md                 # LLM 主要阅读的 Markdown 文档
  document.json               # 结构化文档表示
  manifest.json               # 来源、哈希、页数、引擎、警告和处理记录
  pages/                      # 每页渲染图片，用于视觉核查和多模态 fallback
    page_0001.png
  figures/                    # 提取出的图片、图表或页面资产
  tables/                     # 提取出的表格 CSV / Markdown
  chunks/                     # 面向 RAG 和 Agent 检索的分块
    chunks.jsonl
  logs/
    preflight.json            # PDF 预检查结果
    validation.json           # 转换质量检查结果
```

也就是说，它不是只输出一份 `.txt` 或 `.md`，而是输出一个完整的 **research bundle**。

这个 research bundle 可以直接用于：

- 论文总结；
- 文献综述；
- 多篇论文对比；
- citation-aware 问答；
- RAG 检索；
- Agent 自动研究；
- 多模态核查；
- 表格和图像资产分析；
- 后续的自动引用、实验复现和知识库构建。

---

## 4. 它和普通 PDF 转 Markdown 工具有什么区别？

普通 PDF 转 Markdown 工具通常关注一个问题：

```text
能不能把 PDF 里的文字提出来？
```

PDF2MD-Agent 关注的是另一个问题：

```text
提取出来的内容，能不能被 AI Agent 长期、稳定、可追溯地使用？
```

这两个目标不一样。

对于 AI Agent 来说，Markdown 只是入口，不是全部。真正重要的是：

- 每段内容是否知道自己来自哪一页；
- 图表和表格是否被单独保存；
- 扫描件是否能被检测并进入 OCR 流程；
- 输出是否能被 RAG 系统直接分块；
- 转换过程是否有日志和校验结果；
- 复杂 PDF 是否可以切换不同解析引擎；
- 结果是否能被人类和模型共同复查。

因此，PDF2MD-Agent 的设计原则是：

> **Markdown 是给模型读的，但不是唯一真相。页面图片、结构化 JSON、表格、图像和校验日志一起构成可信的文档上下文。**

---

## 5. 核心能力

### 5.1 PDF 预检查

在正式转换前，工具会先分析 PDF 的基本情况，例如：

- 页数；
- 是否加密；
- 每页文字数量；
- 每页图片数量；
- 页面尺寸；
- 是否可能是扫描件；
- 是否存在高风险页面；
- 是否需要 OCR。

这样可以避免直接把所有 PDF 都丢给同一个解析器，然后盲目相信结果。

---

### 5.2 OCR 自动判断

对于扫描版 PDF 或文字层缺失的页面，PDF2MD-Agent 可以进入 OCR 流程。

它支持三种策略：

```text
--ocr never   # 永不 OCR
--ocr auto    # 自动判断是否需要 OCR
--ocr always  # 总是先 OCR
```

这让它既可以处理正常的 born-digital PDF，也可以处理扫描版文档。

---

### 5.3 Layout-aware Markdown 转换

工具会尽量保留文档结构，包括：

- 标题；
- 段落；
- 列表；
- 表格；
- 链接；
- 代码块；
- 图片位置；
- 页码锚点；
- 多栏阅读顺序。

最终生成的 `document.md` 是下游 LLM 和 Agent 的主要输入。

示例：

```markdown
<a id="page-1"></a>

# Title of the Paper

## Abstract

...

<a id="page-2"></a>

## Method

...
```

这种 page-aware Markdown 能让模型回答问题时更容易引用来源，也能让使用者快速回到原始页面检查。

---

### 5.4 页面图片保留

PDF2MD-Agent 可以把每一页渲染成图片：

```text
pages/page_0001.png
pages/page_0002.png
...
```

这一步非常重要，因为 Markdown 可能无法完整表达复杂布局、图像、公式和表格。

当文本解析结果不确定时，Agent 或使用者可以回看页面图片，进行视觉核查。对于多模态模型来说，这些页面图片也可以作为 fallback 输入。

---

### 5.5 表格和图像资产提取

工具会尽可能把 PDF 中的表格和图片保存成独立资产：

```text
tables/page_0003_table_01.csv
figures/page_0005_img_01.png
```

这样做的好处是：

- 表格可以被程序读取和分析；
- 图像可以被多模态模型单独理解；
- 文献综述时可以复用关键图表；
- 下游 Agent 不需要从混乱文本里猜测表格结构。

---

### 5.6 RAG-ready 分块

PDF2MD-Agent 可以直接生成检索用 chunks：

```text
chunks/chunks.jsonl
```

每个 chunk 会尽量包含：

```json
{
  "id": "source_sha256:p0001:c0001",
  "text": "...",
  "page_start": 1,
  "page_end": 2,
  "source_pdf": "paper.pdf",
  "source_sha256": "..."
}
```

这让它可以直接接入向量数据库、Agent memory、知识库系统或者论文问答系统。

---

### 5.7 Manifest 和校验报告

每次转换都会生成 manifest 和 validation logs。

这些文件记录：

- 原始 PDF 路径；
- 文件哈希；
- 页数；
- 使用的解析引擎；
- 是否经过 OCR；
- 是否渲染页面图片；
- 是否成功提取表格和图像；
- 哪些页面可能存在解析风险；
- 输出文件是否完整。

这让整个文档解析过程可追踪、可复查、可复现。

---

## 6. 为什么你应该使用它？

### 6.1 它让 Agent 读到更可靠的材料

AI Agent 的表现很大程度取决于它读到的上下文。如果 PDF 解析阶段已经漏掉了关键信息，下游总结、问答、推理和引用都会受影响。

PDF2MD-Agent 通过预检查、OCR、layout-aware 转换、页面锚点、资产提取和校验日志，尽量降低这种风险。

---

### 6.2 它让研究结果可追溯

一个好的 AI research workflow 不应该只给出“看起来正确”的总结，还应该能回答：

```text
这句话来自哪一页？
这个表格在哪里？
这个结论是不是原文真的说过？
这个 chunk 是从哪份 PDF 里来的？
```

PDF2MD-Agent 从一开始就把页码、来源和输出结构设计进流程里，让后续的引用和复查更自然。

---

### 6.3 它降低重复劳动

很多人做论文阅读系统时，都会重复写类似代码：

- 下载 PDF；
- 解析 PDF；
- 转 Markdown；
- 切 chunk；
- 做 OCR；
- 处理表格；
- 保存图片；
- 写日志；
- 接入 RAG。

PDF2MD-Agent 把这些步骤抽成一个统一工具，让研究者可以把时间花在模型、算法、实验和应用本身，而不是反复处理 PDF 解析细节。

---

### 6.4 它适合个人，也适合团队

对于个人研究者，它可以作为本地论文阅读和知识库构建工具。

对于团队，它可以作为统一的文档 ingestion 层，让所有人和所有 Agent 使用同一种文档输入格式。

这意味着：

- 结果更稳定；
- 标准更统一；
- 出错更容易定位；
- 后续功能更容易扩展。

---

## 7. 谁会需要这个项目？

PDF2MD-Agent 特别适合以下人群：

### AI / ML 研究者

需要批量阅读论文、做文献综述、追踪技术路线、比较方法和实验结果。

### RAG 系统开发者

需要把 PDF 文档转换成稳定、可追溯、可检索的 chunks。

### Agent 应用开发者

需要让 Agent 自动下载、解析、阅读、总结和比较文档。

### 研究型学生

需要更高效地整理课程论文、博士论文、技术报告和参考文献。

### 工程团队

需要把内部报告、技术文档、白皮书或标准文档接入知识库。

### 开源社区开发者

可以基于这个项目扩展 OCR、表格解析、公式识别、文献元数据抽取、浏览器自动下载和多模态复查等能力。

---

## 8. 一个典型使用流程

### 8.1 检查 PDF

```bash
pdf2md-agent inspect paper.pdf --out output/paper
```

这一步会生成 PDF 预检查结果，帮助你判断文档是否适合直接解析，是否需要 OCR，是否有可疑页面。

---

### 8.2 转换成研究包

```bash
pdf2md-agent convert paper.pdf \
  --out output/paper \
  --engine auto \
  --ocr auto \
  --render-pages \
  --extract-assets \
  --chunk
```

转换完成后，你会得到一个完整的 research bundle。

---

### 8.3 批量处理论文

```bash
pdf2md-agent batch ./papers --out ./converted --engine auto --ocr auto
```

这适合构建个人论文库、课程阅读材料库或团队知识库。当前版本按顺序执行；`--jobs` 参数已保留给未来并行处理。

---

## 9. 设计理念

PDF2MD-Agent 的核心理念可以概括为四句话。

### 9.1 不盲信单一解析器

不同 PDF 的复杂程度不同。正常论文、扫描文档、复杂表格、双栏排版、公式密集文档，需要不同处理策略。

因此，这个项目会支持可插拔解析引擎，而不是把整个流程绑定到一个库上。

---

### 9.2 Markdown 是入口，不是全部

Markdown 对 LLM 友好，但它无法完整表达 PDF 的全部信息。

所以项目会同时保存：

- Markdown；
- JSON；
- 页面图片；
- 表格；
- 图像；
- chunks；
- manifest；
- validation logs。

这比单一文本文件更适合长期研究工作流。

---

### 9.3 默认本地、确定性、低成本

核心转换流程默认不依赖 LLM，也不强制联网。

这样做有几个好处：

- 成本低；
- 速度可控；
- 结果更可复现；
- 适合批量处理；
- 适合私有文档；
- 更容易部署到服务器。

LLM 辅助修复可以作为后续可选功能，但不应该成为基础解析流程的默认依赖。

---

### 9.4 从一开始就考虑 Agent 工作流

这个项目不是为了做一个孤立的转换器，而是为了成为 AI Auto Research 的基础组件。

它服务的是完整链路：

```text
下载论文
  -> 检查 PDF
  -> OCR / 转换
  -> 生成 Markdown 和结构化资产
  -> 分块
  -> 检索
  -> 总结
  -> 问答
  -> 对比
  -> 引用
  -> 复查
```

---

## 10. 可得性：为什么这个项目容易被使用？

PDF2MD-Agent 会尽量保持简单、直接和本地可运行。

### 10.1 标准 CLI

用户不需要理解内部复杂逻辑，只需要运行命令：

```bash
pdf2md-agent convert paper.pdf --out output/paper
```

### 10.2 标准输出格式

输出是通用格式：

- Markdown；
- JSON；
- JSONL；
- CSV；
- PNG；
- YAML / JSON logs。

这些格式可以被 Python、RAG 框架、向量数据库、Web UI、Notebook 和 Agent 系统直接消费。

### 10.3 本地优先

核心流程可以在本地或服务器上运行，不强制依赖云服务。

这对科研、企业内部文档和隐私敏感文档都很重要。

### 10.4 渐进式依赖

基础功能使用轻量依赖即可运行。

更复杂的能力，例如 OCR、Docling、Marker、GROBID、浏览器自动下载，可以作为可选模块逐步开启。

这让新用户可以先快速上手，高级用户可以继续扩展。

---

## 11. 可持续性：为什么这个项目适合长期维护？

开源项目不只是“能跑起来”，还要能长期演进。PDF2MD-Agent 在设计上会尽量保证可持续性。

### 11.1 模块化架构

项目会把功能拆成清晰模块：

```text
preflight
ocr
conversion engines
asset extraction
chunking
validation
manifest
batch processing
```

每个模块都可以单独测试、替换和扩展。

---

### 11.2 可插拔引擎

不同解析器适合不同场景。

项目会支持类似这样的引擎接口：

```text
pymupdf4llm
Docling
Marker
text fallback
GROBID metadata adapter
```

如果某个库更新、失效或不适合某类文档，社区可以添加新的 adapter，而不是重写整个项目。

---

### 11.3 有日志，有校验，有 manifest

每次转换都会留下处理记录。

这对开源项目非常关键，因为用户遇到问题时，可以提供：

- 输入文件信息；
- 使用的 engine；
- OCR 策略；
- 页面统计；
- warning；
- validation 结果。

维护者可以更快定位问题，而不是靠猜。

---

### 11.4 不把核心能力绑定到 LLM API

如果一个文档解析工具默认依赖某个闭源 LLM API，它的成本、速度、可复现性和长期稳定性都会受影响。

PDF2MD-Agent 的核心流程默认不使用 LLM。这样它更适合作为基础设施，也更适合开源社区长期维护。

---

### 11.5 面向社区扩展

这个项目天然适合社区贡献，例如：

- 更好的表格解析；
- 更好的公式识别；
- 更好的 OCR 策略；
- 更多文件格式支持；
- arXiv / Semantic Scholar / Zotero 集成；
- Chrome DevTools MCP 下载论文；
- benchmark 数据集；
- 文档质量评分；
- 多语言文档支持；
- Web UI；
- Docker 部署。

这些扩展方向都可以围绕同一个 research bundle 标准展开。

---

## 12. 这个项目不是什么？

为了避免误解，需要明确几件事。

### 12.1 它不是一个保证 100% 正确的 PDF 解析器

PDF 解析本身很复杂。对于极端复杂的论文、扫描质量很差的文档、公式密集页面和复杂表格，任何工具都可能出错。

PDF2MD-Agent 的目标不是宣称“永远解析正确”，而是：

```text
尽可能提高解析质量，并且把不确定性暴露出来。
```

这也是 manifest、validation logs 和页面图片存在的意义。

---

### 12.2 它不是只给聊天机器人用的工具

它可以服务 ChatGPT、Claude、Gemini、Cursor、Codex、local LLM 和各种 Agent，但它本身更像文档基础设施。

只要你的系统需要把 PDF 变成可检索、可追溯、可复查的材料，它就有价值。

---

### 12.3 它不是把人类从研究中完全替代掉

它帮助你减少低质量重复劳动，但复杂研究仍然需要人的判断。

它更适合做：

```text
文档入口标准化 + 初步结构化 + Agent 下游任务准备
```

而不是替代严肃研究中的全部判断过程。

---

## 13. 未来路线图

### 短期目标

- 完成基础 CLI；
- 支持 PDF inspect；
- 支持 PDF to Markdown；
- 支持页面图片渲染；
- 支持 manifest；
- 支持 chunks 输出；
- 支持 batch 处理；
- 增加基础 validation。

### 中期目标

- 增强 Docling 后端；
- 增强 Marker 后端；
- 增强 OCRmyPDF 集成和测试覆盖；
- 增加 GROBID 元数据和参考文献解析；
- 增加表格质量评估；
- 增加多语言文档支持；
- 增加 benchmark 和测试样例。

### 长期目标

- 支持 Chrome DevTools MCP 自动下载论文；
- 支持 arXiv / Semantic Scholar / Zotero 工作流；
- 支持 Web UI；
- 支持 Docker 部署；
- 支持文档质量评分；
- 支持 LLM-assisted repair；
- 支持多模态 Agent 复查；
- 成为 AI Auto Research 的通用 ingestion layer。

---

## 14. 一个更完整的愿景

未来的 AI Auto Research 不应该是：

```text
把 PDF 扔给模型，然后希望它读对。
```

而应该是：

```text
先把文档变成稳定、可追溯、可校验的研究材料包，
再让模型和 Agent 在这个可靠上下文上工作。
```

PDF2MD-Agent 希望成为这个流程里的第一层基础设施。

它不直接替你完成所有研究，但它让后续研究流程站在更可靠的输入之上。

当每篇论文都可以被转换成统一的 research bundle，当每个 chunk 都可以追溯到原文页面，当每张表格和图像都能被单独复查，当每次转换都有 manifest 和 validation logs，AI Agent 才能真正进入更可信、更可复现、更可扩展的研究工作流。

---

## 15. 适合放在 GitHub 首页的短版介绍

**PDF2MD-Agent is a local-first document ingestion toolkit for AI and Agent research.**

It converts PDF files into LLM-friendly, traceable, and validation-aware research bundles, including Markdown, structured JSON, rendered page images, extracted tables, figures, retrieval-ready chunks, and processing logs.

Instead of asking an Agent to blindly read a PDF, PDF2MD-Agent prepares the document first:

```text
preflight -> OCR if needed -> layout-aware conversion -> asset extraction -> chunking -> validation
```

It is designed for:

- AI paper reading;
- literature review;
- RAG pipelines;
- citation-aware Q&A;
- research agents;
- document knowledge bases;
- multimodal verification.

The project is local-first, modular, reproducible, and extensible. Its goal is to become a reliable ingestion layer for AI Auto Research.

---

## 16. 推荐的开源项目标语

可以从下面几句里选择一句作为项目首页或 README 的 subtitle。

```text
Turn PDFs into reliable research bundles for AI Agents.
```

```text
Stop letting Agents blindly read PDFs. Give them traceable research context.
```

```text
A local-first PDF ingestion pipeline for AI Auto Research.
```

```text
From messy PDFs to structured, traceable, RAG-ready research materials.
```

中文版本：

```text
把复杂 PDF 变成 AI Agent 可以可靠使用的研究材料包。
```

```text
不要让 Agent 盲读 PDF，先给它可追溯的研究上下文。
```

```text
面向 AI Auto Research 的本地优先文档入口。
```

---

## 17. 对贡献者的邀请

PDF2MD-Agent 不是一个封闭工具，而是一个希望和社区共同建设的基础组件。

如果你关心以下问题，欢迎参与：

- 如何让 AI 更可靠地阅读论文；
- 如何构建高质量 RAG 知识库；
- 如何处理复杂 PDF 布局；
- 如何做表格、公式和图像理解；
- 如何让 Agent 的研究过程更可追溯；
- 如何把论文下载、解析、阅读、总结、引用连接成完整闭环。

这个项目的价值不只是“转换 PDF”，而是为 AI research workflow 提供一个更稳定的入口。

让我们一起把 AI Agent 的文档阅读，从“看起来读了”推进到“真的可用、可查、可复现”。
