# DocMark — 文档转 Markdown 智能体技能（Agent Skill）

开源 **Agent Skill**：通过 DocMark API 把 PDF / Word / PPT / Excel 以及图片（发票、身份证、订单截图、通用 OCR）转换为干净的 Markdown。

目录结构遵循业界广泛采用的 **Agent Skills（SKILL.md）** 规范，可无缝放入各类支持 SKILL.md 的智能体生态。同时附有 OpenAI 风格的 `tool-schema.json`，供 function calling 生态使用。

## API 契约（v2）

| 动作 | 接口 | 请求体 |
|---|---|---|
| 健康检查 | `GET {BASE}/health` | — |
| 转换本地文件 | `POST {BASE}/convert` | multipart，字段 `file` |
| 转换远程文件 | `POST {BASE}/convert/url` | JSON `{"url":"https://…"}` |
| 任务进度 | `GET {BASE}/convert/tasks/{taskId}` | — |
| 任务结果 | `GET {BASE}/convert/tasks/{taskId}/result` | — |

鉴权：`Authorization: Bearer <API-Key>`（也兼容 `X-API-Key`）。
支持格式：`.pdf .docx/.doc .pptx/.ppt .xlsx/.xls .jpg .jpeg .png .bmp .webp`。
错误码：`400/401/402/413/415/409/500/503`；计费 1 页 = 1 积分，失败自动退还。

### 大文档异步任务

超过 `ASYNC_MIN_PAGES`（默认 10）页的文档自动转后台任务：`POST /convert` 返回 **202** + `taskId`（此时已按页扣分），
用 `GET /convert/tasks/{taskId}` 看进度、`GET /convert/tasks/{taskId}/result` 取 Markdown（未完成 409）。
任务结果默认保留 24 小时，`?async=0` 可强制同步。完整契约见 `references/api-contract.md`。

脚本已自动轮询，对调用方透明；不想等就用 `--no-poll` 拿 taskId，稍后 `--task <id>` 续取（不会重复扣费）。

## 快速开始

先在 **https://www.prowyg.com** 注册并获取 API Key（新用户注册送 100 积分；积分不足可在此充值），然后：

```bash
export DOCMARK_API_KEY=md_your_key

# 本地文件
python3 scripts/convert.py --file invoice.pdf -o invoice.md

# 远程 URL（走 /convert/url）
python3 scripts/convert.py --url https://example.com/a.pdf -o a.md

# 大文档（>10 页）：自动转异步并轮询到出结果
python3 scripts/convert.py --file 278页扫描件.pdf -o big.md

# 不想等：先拿 taskId，稍后续取（不会重复扣费）
python3 scripts/convert.py --file 大文件.pdf --no-poll
python3 scripts/convert.py --task a1e669891d1c -o out.md

# 自托管
DOCMARK_BASE=https://your-host python3 scripts/convert.py --file a.pdf
```

## 目录结构

```
docmark-md-converter/
├── SKILL.md                  # 技能定义（智能体按需加载；含触发场景、异步任务、失败处置、常见坑）
├── README.md                 # 本文件（人看的说明）
├── tool-schema.json          # OpenAI 风格 function-calling schema（含 task / no_poll）
├── scripts/convert.py        # 转换脚本（纯 Python 标准库，无第三方依赖）
├── examples/README.md        # 调用示例 + 真实输出（含表格还原前后对比）
├── references/api-contract.md# 完整接口契约（异步任务、错误码全表、格式矩阵）
├── tests/test_convert.py     # 离线自检（本地假服务，不联网、不需要 Key）
└── LICENSE
```

## 安装到智能体

把整个文件夹复制到目标智能体的 skills 目录即可，例如：

```
~/.claude/skills/docmark-md-converter/
~/.config/opencode/skills/docmark-md-converter/
```

## 自检

不需要 API Key、不联网：

```bash
python3 tests/test_convert.py     # 应输出 ALL TESTS PASSED
```

## 许可证  

MIT
