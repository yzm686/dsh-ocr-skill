# DocMark — 文档转 Markdown 智能体技能（Agent Skill）

开源 **Agent Skill**：通过 DocMark API 把 PDF / Word / PPT / Excel 以及图片（发票、身份证、订单截图、通用 OCR）转换为干净的 Markdown。

目录结构遵循业界广泛采用的 **Agent Skills（SKILL.md）** 规范，可无缝放入各类支持 SKILL.md 的智能体生态。同时附有 OpenAI 风格的 `tool-schema.json`，供 function calling 生态使用。

## API 契约（v2）

| 动作 | 接口 | 请求体 |
|---|---|---|
| 健康检查 | `GET {BASE}/health` | — |
| 转换本地文件 | `POST {BASE}/convert` | multipart，字段 `file` |
| 转换远程文件 | `POST {BASE}/convert/url` | JSON `{"url":"https://…"}` |

鉴权：`Authorization: Bearer <API-Key>`（也兼容 `X-API-Key`）。
支持格式：`.pdf .docx/.doc .pptx/.ppt .xlsx/.xls .jpg .jpeg .png .bmp .webp`。
错误码：`400/401/402/413/415/500/503`；计费 1 页 = 1 积分，失败自动退还。

## 快速开始

先在 **https://www.prowyg.com** 注册并获取 API Key（新用户注册送 100 积分；积分不足可在此充值），然后：

```bash
export DOCMARK_API_KEY=md_your_key

# 本地文件
python3 scripts/convert.py --file invoice.pdf -o invoice.md

# 远程 URL（走 /convert/url）
python3 scripts/convert.py --url https://example.com/a.pdf -o a.md

# 自托管
DOCMARK_BASE=https://your-host python3 scripts/convert.py --file a.pdf
```

## 安装到智能体

把整个文件夹复制到目标智能体的 skills 目录即可，例如：

```
~/.claude/skills/docmark-md-converter/
~/.config/opencode/skills/docmark-md-converter/
```

## 测试

```bash
python3 tests/test_convert.py     # 本地假服务自测，无需 API Key
```

## 许可证

MIT
