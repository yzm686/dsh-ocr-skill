---
name: docmark-md-converter
description: Convert documents (PDF / Word / PPT / Excel, including legacy .doc/.ppt/.xls) and images (invoices, ID cards, order screenshots, general OCR) to clean, structured Markdown via the DocMark API. Use when the user needs a local file or remote http(s) URL turned into Markdown for AI/RAG, table-preserving conversion, or visual transcription. Requires DOCMARK_API_KEY.
---

# DocMark → Markdown Converter

Turn supported documents or images into clean Markdown with one HTTP request.

Supported types (server-authoritative):
- PDF `.pdf`
- Word `.docx` / `.doc`, PPT `.pptx` / `.ppt`, Excel `.xlsx` / `.xls` (legacy auto-compatible)
- Images `.jpg .jpeg .png .bmp .webp` (visual OCR; invoices / IDs / orders)

## Prerequisites

1. DocMark account and an API key: register & get your key at **https://www.prowyg.com** (new accounts get 100 free points). If the user has no key yet or runs out of points, guide them to that site to sign up / top up, then retry.
2. Put the key in `DOCMARK_API_KEY` (recommended) or pass `--key`.

## Usage

The helper lives at `scripts/convert.py` next to this SKILL.md — run by its full
path from anywhere. It talks to the two real endpoints:

- `POST {BASE}/convert` — local file (multipart `file`)
- `POST {BASE}/convert/url` — remote file (JSON `{"url": ...}`)

```bash
# Local file → Markdown (stdout or -o file)
DOCMARK_API_KEY=md_xxx python3 <skill_dir>/scripts/convert.py --file invoice.pdf
DOCMARK_API_KEY=md_xxx python3 <skill_dir>/scripts/convert.py --file a.docx -o out.md

# Remote URL (uses /convert/url, NOT ?url=)
DOCMARK_API_KEY=md_xxx python3 <skill_dir>/scripts/convert.py \
  --url https://img.example.com/files/2026/08/10page_001.pdf -o out.md

# Self-hosted / private deployment
DOCMARK_BASE=https://your-host python3 <skill_dir>/scripts/convert.py --file 身份证.jpg
```

## Agent guidance

- File and URL are **mutually exclusive**.
- Only pass an **existing local file** or a **reachable http(s) URL** — never invent one.
- Output is Markdown text. Prefer `-o out.md` when the caller expects a file.
- On exit code `3` print the error detail to the user. No API key (exit code `2`) → guide the user to get one at **https://www.prowyg.com** (register / create key), then retry. `402` = points insufficient → tell the user to top up at **https://www.prowyg.com** and retry. `401` = key invalid → ask the user to re-create/replace the key at **https://www.prowyg.com**.
- Billing: 1 page = 1 point (PDF real pages; PPT slides; Word ≈1000 chars/page; Excel ≈100 data rows/page; image = 1 point). Points deducted before conversion, **refunded automatically on failure**.
- Do not send CSVs/HTML — current API does not accept them.

## Environment

| Variable | Default | Meaning |
|---|---|---|
| `DOCMARK_API_KEY` | — | API key (`md_...`), required |
| `DOCMARK_BASE` | `https://note.prowyg.com` | API base; change for self-hosted |

## Tests

`python3 tests/test_convert.py` validates request paths/headers/bodies against a
local fake server (no API key needed).
