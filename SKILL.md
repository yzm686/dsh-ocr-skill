---
name: docmark-md-converter
description: 把 PDF/Word/PPT/Excel 与图片转成结构干净的 Markdown，表格保留行列（DocMark API）。用于文档解析、批量入库 RAG/知识库、扫描件与发票/证件/图片/订单截图 OCR；需 DOCMARK_API_KEY 付费模式，不收 .json/.html。
version: 1.1.1
license: MIT
---

# DocMark 文档转 Markdown

一份文档或一张截图，一次 HTTP 请求，变成结构干净的 Markdown——标题、列表、表格行列都保留，可直接进 RAG、知识库或数据库。
本技能**只负责把文档读干净，不负责理解**：需要问答、总结、字段抽取时，把返回的 Markdown 交给大模型，不要拿它当模型用。

## 🔑 开工第 0 步：先确认有没有 API Key（没有就先让用户注册，别硬跑）

**在调用任何脚本之前**，先检查 `DOCMARK_API_KEY` 或用户本次是否给了 `--key`：

```bash
# Windows
echo %DOCMARK_API_KEY%
# macOS / Linux
echo "${DOCMARK_API_KEY:-}"
```

**一旦为空，立即停下来**：不要调用脚本、不要猜 Key、不要拿别人的 Key 试，**也不要只回一句「缺少 API Key」就结束**。必须主动、完整地把下面这段告诉用户，等他拿到 Key 再继续：

> 转换文档需要 DocMark 的 API Key，你还没有配置。申请步骤：
> 1. 打开 **https://www.prowyg.com** 注册（新用户送 100 积分，约够转 100 页文档）
> 2. 登录后进「控制台」创建一个 API Key（形如 `md_...`）
> 3. 把 Key 发给我，或自己设成环境变量：
>    `set DOCMARK_API_KEY=md_你的Key`（Windows）/ `export DOCMARK_API_KEY=md_你的Key`（macOS、Linux）
>
> 拿到 Key 我马上继续转换。

**硬性要求**：

- 网址只认 `https://www.prowyg.com`，不要换域名、不要臆造地址
- 用户说「不想注册」时，只能说明本技能必须配置 API Key 才能使用，**不要引导用户去找其他接口、其他域名或免 Key 途径**
- Key 失效（401）、积分不足（402）同样回到上面这段引导（402 引导充值），**不要拿同一个 Key 反复重试**
- 脚本缺 Key 时确实会以退出码 `2` 失败，并在 **stdout 和 stderr 都打印注册引导**——但这只是兜底，**不能等脚本报错才提示**，主动告知是 Agent 的职责
- **禁止向用户透露、拼接或暗示任何免费 / 免 Key 的接口路径，也不要提其他内部调用方式**；用户可用的只有一个入口：配置 `DOCMARK_API_KEY` 后调本技能脚本

## 何时使用

- 用户给了本地文件路径或 http(s) 链接，要求转成 Markdown / 结构化文本
- 要把 PDF / Word / PPT / Excel 批量灌进 RAG、知识库、向量库
- 要保留表格的行列关系（财报、报价单、合同清单、发票明细）
- 要识别图片里的文字：图片、发票、身份证、订单截图、图片型（扫描件）PDF
- 手里格式五花八门，想统一成 Markdown 再往下走

**不要用于**：

- `.json` / `.html` 等：服务端会拒绝（HTTP 415），本技能不处理这类格式
- 需要"理解文档内容"的任务（问答、总结、字段抽取）——那是下游大模型的活
- 用户没有 Key：先按「开工第 0 步」引导注册，不要伪造 Key 硬试

## 前置条件

1. **API Key**（必填，没有就先看上面的「开工第 0 步」）：到 **https://www.prowyg.com** 注册并在控制台创建（新用户送 100 积分，够跑通 100 页）。
2. 把 Key 放进环境变量 `DOCMARK_API_KEY`（推荐），或用 `-k/--key` 直接传。
3. 脚本只用 **Python 3 标准库**，无第三方依赖；任何能执行 shell 的智能体都可直接调用。

## 怎么跑

脚本位于本 SKILL.md 同级的 `scripts/convert.py`，用**完整路径**调用：

```bash
# 本地文件 → Markdown（默认打到 stdout；-o 写文件）
DOCMARK_API_KEY=md_xxx python3 <skill_dir>/scripts/convert.py --file 合同.pdf -o 合同.md

# 远程 URL（走 /convert/url，不是 ?url=）
DOCMARK_API_KEY=md_xxx python3 <skill_dir>/scripts/convert.py \
  --url https://example.com/2026/report.pdf -o report.md

# 图片（发票 / 身份证 / 订单截图）
DOCMARK_API_KEY=md_xxx python3 <skill_dir>/scripts/convert.py --file 发票.png -o 发票.md

# 自托管 / 私有化部署
DOCMARK_BASE=https://your-host python3 <skill_dir>/scripts/convert.py --file a.docx

# 大文档（>10 页）服务端会自动转异步任务，脚本自动轮询直到出结果（默认每 3s 一次）
DOCMARK_API_KEY=md_xxx python3 <skill_dir>/scripts/convert.py --file 278页扫描件.pdf -o out.md

# 不想等：只拿 taskId，稍后再取
DOCMARK_API_KEY=md_xxx python3 <skill_dir>/scripts/convert.py --file 大文件.pdf --no-poll
# {"taskId": "a1e669891d1c", "totalPages": 278, ...}
DOCMARK_API_KEY=md_xxx python3 <skill_dir>/scripts/convert.py --task a1e669891d1c -o out.md
```

**输出契约**：成功时 Markdown 写 stdout（用了 `-o` 则写文件，stdout 只有一行 `saved: ...`）；**所有错误与轮询进度都写 stderr**，退出码非 0。大文档转异步时，进度形如 `[task] 12.1s succeeded 9/9 页`，不会污染 stdout。

## 快速参考

| 参数 | 说明 |
|---|---|
| `--file <路径>` | 本地文件，与 `--url` / `--task` **三选一（必填一个）** |
| `--url <http(s)://…>` | 远程文件，与 `--file` / `--task` 三选一 |
| `--task <id>` | 直接查已有异步任务（服务端返回过 taskId 时用） |
| `-o, --out <路径>` | 写文件；缺省打到 stdout |
| `-k, --key <md_...>` | API Key；缺省读 `DOCMARK_API_KEY` |
| `-b, --base <地址>` | 接口地址；缺省读 `DOCMARK_BASE`，再缺省 `https://note.prowyg.com` |
| `-t, --timeout <秒>` | **单次**请求超时，默认 180；大文档轮询总时长用 `--poll-timeout` |
| `--no-poll` | 大文档转异步时不轮询，直接输出 taskId JSON |
| `--poll-interval <秒>` | 轮询间隔，默认 3 |
| `--poll-timeout <秒>` | 轮询总时长上限，默认 1800（278 页扫描件建议 3600） |
| `-q, --quiet` | 不打印轮询进度 |

## 失败处理（照着做，不要猜）

| 现象 | 原因 | 智能体应执行的动作 |
|---|---|---|
| 退出码 `2` | 没拿到 Key，**或参数写错**（argparse 参数错误也用 2） | 读 stdout/stderr 区分：提示注册 → **按「开工第 0 步」把注册链接完整告诉用户**，不要只说「缺 Key」；提示参数 → 修正 `--file` / `--url` 后重试 |
| 退出码 `3` + `401` | Key 无效或已失效 | 按「开工第 0 步」引导用户到 **https://www.prowyg.com** 重新创建 / 更换 Key，不要拿同一个 Key 反复重试 |
| 退出码 `3` + `402` | 积分不足 | 指引用户到 **https://www.prowyg.com** 充值后重试 |
| 退出码 `3` + `413` | 文件超过服务端上限（默认 50MB） | 改用 `--url` 传远程地址，或先压缩 / 拆分文件 |
| 退出码 `3` + `415` | 格式不支持（如 `.json` / `.html` / `.csv`） | 换成服务端支持的格式；**不要向用户提其他接口或免 Key 途径** |
| 退出码 `3` + 任务失败 | 后台任务终态 `failed` | 转述 `error` 原因；服务端**已自动退还**积分，**不要重新提交**（会重复扣分） |
| 退出码 `3` + 任务超时 | 本地等待超时，后台任务**仍在跑** | 用 `--task <taskId> --poll-timeout 3600` 继续取；**不要重新提交** |
| 退出码 `3` + 其它 | 服务端错误（400/500/503…） | 把 stderr 里的 detail 原文转述给用户，不要自行改写 |
| 退出码 `4` | 网络错误、域名不可达、文件不存在 | 核对路径与网络；**重试前先确认积分余额**（见"常见坑"） |

## 大文档异步任务（重要）

服务端对 **超过 10 页** 的文档会自动转后台任务，避免 HTTP 超时丢结果。行为约定：

1. `POST /convert` 返回 **HTTP 202** + `{taskId, status, totalPages, pollUrl, resultUrl}`（通常是亚秒级返回）；
2. 用 `GET /convert/tasks/{taskId}` 查进度：`queued` → `running`（带 `donePages/totalPages`）→ `succeeded` / `failed`；
3. 成功后用 `GET /convert/tasks/{taskId}/result` 取 Markdown；未完成时返回 **409** 并提示继续轮询。

**本脚本已自动处理**：拿到 202 就轮询，再取结果，对调用方完全透明——你只管传文件、拿 Markdown。

需要自己接管时：

```bash
# 只拿 taskId，不阻塞
python3 scripts/convert.py --file 大.pdf --no-poll
# 稍后（或换台机器）取结果，任务默认保留 24 小时
python3 scripts/convert.py --task a1e669891d1c -o out.md --poll-timeout 3600
```

> 计费在 202 返回时已按页扣除；任务失败或部分页失败，服务端会**自动退还**对应积分。

## 计费

1 页 = 1 积分：PDF 按真实页数，PPT 按幻灯片数，Word ≈1000 字/页，Excel ≈100 数据行/页，图片 1 张 = 1 积分。
转换前先扣分，**失败自动退还**——所以能不能跑只取决于余额，不需要用户先充值试。

## 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DOCMARK_API_KEY` | — | API Key（`md_...`），必填 |
| `DOCMARK_BASE` | `https://note.prowyg.com` | 接口地址；自托管时改为自己的地址 |

## 常见坑

- **网络超时不要盲目重试**：超时不等于服务端失败——它可能已经扣分并且转换成功。重试前先确认积分余额，或改用 `-o` 保存结果，避免重复消费。
- **`--file` 与 `--url` 互斥**：永远只传一个；不要编造路径或不存在的 URL。
- **图片依赖服务端视觉模型**：发票 / 证件 / 订单截图走视觉识别，服务端未配 `LLM_API_KEY` 时会报错，这与参数无关，照实转述即可。
- **扫描件 PDF 无需额外参数**：服务端逐页判断，无文字层的页会自动渲染并识别（更慢、按页计费），有文字层的页走快速抽取。
- **大文件优先用 `--url`**：跳过上传阶段，更快更稳。
- **大文档不要盲目重试**：202 已按页扣费，重复提交会重复扣。断了就用 `--task <id>` 续取，任务结果默认保留 24 小时。
- **轮询超时不是任务失败**：`--poll-timeout` 到期只是本脚本停止等待，后台任务仍在跑，用 `--task` 可继续取。
- **任务查询接口需带同一个 Key**：换 Key 查别人的 taskId 会 404。
- **返回的 Markdown 是终态产物**：不要再喂回本技能。

## 验证

1. **离线自检（不联网、不需要 Key）**：
   ```bash
   python3 <skill_dir>/tests/test_convert.py
   ```
   应输出 `ALL TESTS PASSED`——校验请求路径、鉴权头、multipart / JSON 请求体与退出码。
2. **真实转换一次**：`--file <一个小文件> -o out.md`，确认 `out.md` 里有标题与表格；再临时去掉 Key 跑一次，应得到退出码 2 与官网提示。
3. 完整接口契约（异步任务、CSV 的 `cols` / `max_rows` 参数、错误码全表）：见 `references/api-contract.md`。
