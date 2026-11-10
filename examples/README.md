# DocMark 示例：把文档和图片转成干净 Markdown

本目录给出可直接复制的调用示例与**真实输出**，内容来自本机跑通的实际结果，未做美化修饰。

## 1. 常用命令

```bash
# 合同 / 财报类 PDF（表格按 Markdown 表格还原）
DOCMARK_API_KEY=md_xxx python3 scripts/convert.py --file 合同.pdf -o 合同.md

# 发票 / 身份证 / 订单截图等图片（走视觉识别）
DOCMARK_API_KEY=md_xxx python3 scripts/convert.py --file 发票.png -o 发票.md
DOCMARK_API_KEY=md_xxx python3 scripts/convert.py --file 身份证.jpg -o 身份证.md

# Word / PPT / Excel（旧版 .doc/.ppt/.xls 由服务端自动兼容）
DOCMARK_API_KEY=md_xxx python3 scripts/convert.py --file 报价单.xlsx -o 报价单.md

# 远程文件（走 /convert/url，不是 ?url=）
DOCMARK_API_KEY=md_xxx python3 scripts/convert.py --url https://example.com/a.pdf -o a.md

# 自托管 / 私有化部署
DOCMARK_BASE=https://your-host python3 scripts/convert.py --file a.docx -o a.md
```

不传 `-o` 时，Markdown 直接打印到 stdout，方便管道处理：

```bash
DOCMARK_API_KEY=md_xxx python3 scripts/convert.py --file 合同.pdf > 合同.md
```

## 2. 表格还原前后（真实对比）

同一页 100 页中文合同，同一个解析内核，差别只在有没有做表格还原。

**不做表格还原、直接抽文本**——表头和数据被拍平成一行行空格分隔的文本，列关系只能靠数空格猜：

```text
序号 物料编码 品名规格 单位 数量 含税单价(元) 金额(元) 交货日期
1 MAT-02001 工业级路由器 R100 型（双频 千兆） 台 3 1,280.50 3,841.50 2026-02-02
2 MAT-02002 工业级路由器 R200 型（双频 千兆） 台 6 1,417.75 8,506.50 2026-03-03
3 MAT-02003 工业级路由器 R300 型（双频 千兆） 台 9 1,555.00 13,995.00 2026-04-04
```

**接口返回（`/convert`）**——表头、分隔行、数据行齐全，行列结构保留，可直接进 RAG / 数据库 / Excel：

```markdown
| 序号 | 物料编码 | 品名规格 | 单位 | 数量 | 含税单价(元) | 金额(元) | 交货日期 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | MAT-02001 | 工业级路由器 R100 型（双频 千兆） | 台 | 3 | 1,280.50 | 3,841.50 | 2026-02-02 |
| 2 | MAT-02002 | 工业级路由器 R200 型（双频 千兆） | 台 | 6 | 1,417.75 | 8,506.50 | 2026-03-03 |
| 3 | MAT-02003 | 工业级路由器 R300 型（双频 千兆） | 台 | 9 | 1,555.00 | 13,995.00 | 2026-04-04 |
```

> 参考实测：同一份 100 页含表格合同，本机（16 核 / 32G，单并发）最短 1.51 秒完成，返回约 11.6 万字 Markdown，
> 全篇表格均还原为 Markdown 表格。官方公开数据（8 核 8G / 8 并发）为 100 页 6.9 秒。

## 3. 图片识别输出形状（发票示例）

```markdown
| 字段 | 值 |
| --- | --- |
| 发票代码 | 044001900111 |
| 发票号码 | 56789012 |
| 开票日期 | 2026-09-07 |
| 销售方 | 某某公司 |
| 价税合计 | ¥1234.00 |
```

发票、身份证、订单截图各消耗 **1 积分**（与"1 页 = 1 积分"一致）。

## 4. 常见返回与处理

| 现象 | 含义 | 处理 |
|---|---|---|
| 退出码 2 | 缺 API Key，或参数写错 | 到 https://www.prowyg.com 取 Key；或修正 `--file` / `--url` |
| 401 | Key 无效 | 官网重新创建 Key |
| 402 | 积分不足 | 官网充值后重试（失败会自动退分） |
| 413 | 文件超过服务端上限（默认 50MB） | 改用 `--url`，或先压缩 / 拆分 |
| 415 | 格式不支持（不含 `.json/.html/.csv`） | 换成服务端支持的格式 |
| 退出码 4 | 网络错误 / 文件不存在 | 核对路径与网络；重试前先确认积分余额 |
