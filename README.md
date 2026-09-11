<div align="center">

# DocMark · 文档转 Markdown 智能体技能

**PDF / Word / PPT / Excel / 图片 → 干净 Markdown**

一个开源的 **Agent Skill（SKILL.md）**：把本地文件或远程 URL 一键解析成结构化、保留表格的 Markdown，供 **AI 智能体 / RAG / LLM / 大模型** 直接使用。

[中文](./README.md) · English | [官网注册 & 获取 API Key](https://www.prowyg.com) | MIT License

</div>

---

DocMark-md-converter is an **open-source Agent Skill** that turns documents
( PDF, Word, PowerPoint, Excel, and images like invoices / ID cards / orders )
into **clean, table-preserving Markdown** through one HTTP request to the
DocMark API. Built for the **Anthropic Agent Skills (SKILL.md)** convention, it
drops into any SKILL.md-compatible agent — **Claude Code / Claude Desktop,
opencode, OpenAI Codex, Cursor, Zed, Gemini CLI, Cline, Roo, Trae, Qwen Code**
and more — for document parsing, OCR transcription, and RAG ingestion.

> DocMark 文档解析技能：将 PDF/Word/PPT/Excel 与图片（发票、身份证、订单截图、通用 OCR）通过 DocMark API 转换为干净、保留表格结构的 Markdown，供智能体解析文档与 RAG 知识库使用。遵循业界通用 **Agent Skills（SKILL.md）** 规范，开箱即用；同时附带 OpenAI 风格 `tool-schema.json` 供 function calling 生态调用。

## ✨ Features / 特性

| 能力 | 说明 |
|---|---|
| 📄 PDF | 页级并行抽取，保留版式与表格 |
| 📝 Word / PPT / Excel | `.docx/.doc .pptx/.ppt .xlsx/.xls`，旧版 Office 自动兼容 |
| 🖼️ 图片 OCR | 发票 / 身份证 / 订单 / 通用 OCR（`.jpg .jpeg .png .bmp .webp`） |
| 🌐 本地 or 远程 | 本地文件上传 或 `http(s)` URL 直转 |
| 🧹 干净 Markdown | 适合 **RAG / LLM / 知识库** 二次消费 |
| 🔌 跨智能体 | SKILL.md 通用格式 + `tool-schema.json` |

## 🚀 Quick Start / 快速开始

1. 到官网 **https://www.prowyg.com** 注册并获取 API Key（新用户送 100 积分；积分不足在此充值）。
2. 设置环境变量后运行：

```bash
export DOCMARK_API_KEY=md_your_key

# 本地文件 → Markdown（打印到 stdout 或 -o 存文件）
python3 scripts/convert.py --file invoice.pdf -o invoice.md

# 远程 URL → Markdown
python3 scripts/convert.py --url https://example.com/a.pdf -o a.md

# 自托管服务
DOCMARK_BASE=https://your-host python3 scripts/convert.py --file a.docx
```

> Windows PowerShell：
> ```powershell
> $env:DOCMARK_API_KEY="md_your_key"
> python scripts\convert.py --file invoice.pdf -o invoice.md
> ```

## 📥 Install into your agent / 安装到智能体

将本仓库 `SKILL.md` 所在目录作为技能目录接入（复制或加为子目录均可）：

```text
# Claude Code
~/.claude/skills/docmark-md-converter/

# opencode
~/.config/opencode/skills/docmark-md-converter/

# OpenAI Codex
~/.codex/skills/docmark-md-converter/

# Cursor / Zed / Windsurf / Roo / Gemini CLI ...（.agents/skills 或对应 skills 目录）
.agents/skills/docmark-md-converter/
```

也可以把本仓库 `clone` 到项目内 `skills/docmark-md-converter/` 随代码分发。安装后，让智能体"把这份发票/PDF 转成 Markdown"即可自动调用本技能。

## 📡 API Contract / 接口契约（v2）

| Action | Endpoint | Body |
|---|---|---|
| Health | `GET {BASE}/health` | — |
| Convert local file | `POST {BASE}/convert` | multipart, field `file` |
| Convert remote file | `POST {BASE}/convert/url` | JSON `{"url":"https://…"}` |

- Auth：`Authorization: Bearer <API-Key>`（兼容 `X-API-Key`）
- Supported：`.pdf .docx/.doc .pptx/.ppt .xlsx/.xls .jpg .jpeg .png .bmp .webp`
- Errors：`400/401/402/413/415/500/503`；Billing：1 页 = 1 积分，失败自动退还
- 默认服务：`https://note.prowyg.com`（可用 `DOCMARK_BASE` 覆盖为自托管地址）

> 该接口契约可独立于智能体使用——任何能发 HTTP 的语言/工具都能对接，方便二次集成到自建 RAG / 工作流。

## 📦 What's inside / 目录结构

```
docmark-md-converter/
├── SKILL.md            # Agent Skills 技能定义（frontmatter：name/description）
├── README.md           # 本说明（中英双语）
├── tool-schema.json    # OpenAI 风格 function-calling schema
├── scripts/convert.py  # 转换助手（仅用 Python 标准库）
├── examples/README.md  # 发票/身份证等输出示例
├── tests/              # 自测
└── LICENSE             # MIT
```

## 🧭 Ecosystem / 生态适配

| Agent | 是否原生支持 SKILL.md | 接入方式 |
|---|---|---|
| Claude Code / Claude Desktop | ✅ | 见上方 skills 目录 |
| opencode | ✅ | `~/.config/opencode/skills/` |
| OpenAI Codex | ✅ | `~/.codex/skills/` |
| Cursor / Zed / Windsurf / Roo / Gemini CLI / Trae / Qwen Code | ✅ | `.agents/skills/` 或各自 skills 目录 |
| function-calling 平台（OpenAI/国产大模型 API） | ⚡ | 读取 `tool-schema.json` 自行实现 HTTP 调用 |


## 📄 License

[MIT](./LICENSE) © DocMark · 官网 [https://www.prowyg.com](https://www.prowyg.com)
