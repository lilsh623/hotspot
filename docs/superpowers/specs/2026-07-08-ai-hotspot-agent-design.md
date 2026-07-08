# AI 技术热点汇总 Agent — 设计文档

**日期**：2026-07-08
**项目**：hotspot-github

## 1. 目标

每日北京时间 9:30 自动抓取 AI/技术热点，用通义千问 Qwen 生成中文重点摘要，通过 SMTP 邮件推送给单一收件人。整个流程由 GitHub Actions 定时驱动，无需自建服务器。

## 2. 需求画像

- **内容来源**：社区聚合站（Hacker News）+ GitHub Trending + RSS/官方博客
- **摘要引擎**：通义千问 Qwen（`qwen-plus`，OpenAI 兼容接口），只做翻译 + 摘要 + 写总览，不做筛选
- **邮件**：SMTP 发送，HTML + 纯文本双版本，单一收件人
- **调度**：GitHub Actions cron，每日约北京时间 9:30
- **邮件形态**：顶部一段中文总览 + 按来源分组的条目列表
- **去重**：持久化"已推送 URL"记录（`state/seen.json` 提交回仓库），每条热点只推一次

## 3. 整体架构与数据流

单向管道，一次性执行完退出：

```
[调度] GitHub Actions cron (UTC 01:30 = 北京 09:30, 需 contents:write 权限)
   │
   ▼
main.py ──读取──▶ config.py (环境变量: Qwen key, SMTP, 收件人)
   │
   ├──读取──▶ state/seen.json   (已推送 URL 记录 + 时间戳, 仓库内文件)
   │
   ▼
sources/*  每个抓取器 fetch() ──▶ list[Item]   (并发抓取, 单源失败跳过)
   │                                Item = {title, url, source, published_at, raw_text, score}
   ▼
pipeline.py  合并 ──▶ URL 规范化去重(同批次内) ──▶ 剔除 seen.json 中已推送的
   │
   ▼
summarizer.py  候选列表喂给 Qwen ──▶ {overview, items:[{zh_title, zh_summary, url, source}]}
   │
   ▼
render.py  HTML+纯文本模板 ──▶ 邮件正文       mailer.py  SMTP 发送 ──▶ 收件人
   │
   ▼
state.py  发送成功后写入 seen.json + 清理 >30 天记录 ──▶ Actions 自动 commit 回仓库
```

### 关键设计点

- **持久化去重**：`state/seen.json` 存"已推送过的 URL + 推送日期"。每条热点只推一次，跨天有效。
- **状态自清理**：每次运行删除 30 天前的记录，文件大小稳定，不无限膨胀。
- **写回时机**：只有邮件发送成功后才更新 seen.json 并 commit。避免"记了但没发出去"导致漏推。
- **容错**：抓取源单个失败跳过并记日志；Qwen/SMTP 失败则整体失败且不写状态（下次重试这批内容），Actions 标红通知。
- **Item** 是贯穿全程的统一数据结构，各模块只依赖它，互不知道彼此内部实现。

## 4. 抓取源与 Item 数据结构

### 统一 Item 结构

```python
Item = {
  "title":        str,          # 原始标题（可能是英文）
  "url":          str,          # 原文链接（去重主键，会规范化）
  "source":       str,          # 来源标识，如 "HackerNews" / "GitHub" / "OpenAI Blog"
  "published_at": datetime,     # 发布/上榜时间（带时区，统一转 UTC）
  "raw_text":     str,          # 摘要/正文片段，喂给 Qwen 用（可能为空）
  "score":        int | None,   # 热度信号：HN 分数 / GitHub star 数等，用于排序，无则 None
}
```

### 三类抓取器

每个一个文件，实现同一个 `fetch() -> list[Item]` 接口：

| 抓取器 | 数据来源 | 抓取方式 | 热度信号 |
|--------|---------|---------|---------|
| `rss.py` | 官方博客/arXiv（OpenAI、Anthropic、Google AI 等，URL 列表可配置） | 标准 RSS/Atom 解析（`feedparser`） | 无（靠时间新鲜度） |
| `hackernews.py` | Hacker News 前 N 条，按关键词过滤 AI 相关 | 官方 Firebase API（无需 key） | HN 分数 |
| `github_trending.py` | GitHub Trending 当日热门仓库，过滤 AI/ML 相关 | 抓取 trending 页面 HTML 解析（`beautifulsoup4`） | 当日新增 star |

### 关键设计点

- **可插拔**：`sources/__init__.py` 维护抓取器注册列表，`pipeline.py` 遍历。加新源 = 新增一个文件 + 注册一行。
- **AI 相关性初筛**：HN 和 GitHub Trending 内容庞杂，先用宽泛关键词列表（`ai, llm, gpt, agent, model, diffusion...`，可配置）做粗筛，减少噪音和 token 成本。不限定细分领域。
- **单源隔离**：每个 `fetch()` 内部自己 try/except，失败返回空列表并记日志，绝不抛异常中断管道。
- **URL 规范化**：去重前统一处理（去 `utm_` 等追踪参数、去尾部斜杠、统一小写域名），避免同一文章因 URL 差异被当成两条。
- **已知风险**：GitHub Trending 无官方 API，靠 HTML 解析，页面改版时可能失效，需偶尔维护。已接受。

## 5. 取数、筛选与 Qwen 摘要

### 阶段一：程序取数（简单、确定性）

```
每个源各取 8-10 条（可配置，默认 10）：
  ├─ HackerNews      → 按 HN 分数排序取前 N
  ├─ GitHub Trending → 按当日新增 star 排序取前 N
  └─ RSS/官方博客     → 按发布时间取最新 N
合并 → URL 规范化去重(同批) → 剔除 seen.json 已推送的 → 候选列表(约 20-30 条)
```

取数逻辑全在程序里，确定、可预测，不依赖模型主观判断。

### 阶段二：Qwen 只做翻译 + 摘要（不做筛选）

```
输入：候选列表全部条目 {标题, 来源, 正文片段}
任务：
  1. 为每一条生成：中文标题 + 2-3 句中文摘要
  2. 写一段全局中文总览（今日 AI/技术圈整体动态）
输出：结构化 JSON {overview, items:[{zh_title, zh_summary, url, source}]}
     items 按来源分组、保持输入顺序
```

### 关键设计点

- Qwen 职责收窄为**翻译 + 摘要 + 写总览**，一次调用完成，省 token、快。
- 强制 JSON 输出（Qwen `response_format`），`summarizer.py` 直接解析。解析失败则整体失败、不写状态、下次重试。
- prompt 明确要求：摘要客观、不夸大、保留关键数字/模型名/公司名。
- 去重后候选不足也照常发，不硬凑。

## 6. 邮件渲染与发送

### 邮件形态（HTML，"总览 + 分组条目"）

```
┌─────────────────────────────────────────┐
│  AI 技术热点日报 · 2026-07-08              │  ← 标题栏
├─────────────────────────────────────────┤
│  今日总览                                  │
│  今天 AI 圈的整体动态……(Qwen 生成的一段中文) │  ← overview
├─────────────────────────────────────────┤
│  Hacker News                              │  ← 来源分组标题
│  1. 【中文标题】                           │
│     2-3 句中文摘要……                       │
│     🔗 阅读原文 (超链接到 url)              │
│  ...                                      │
│  GitHub Trending                          │
│  官方博客 / RSS                            │
├─────────────────────────────────────────┤
│  共 N 条 · 由 hotspot-github 自动生成       │  ← 页脚
└─────────────────────────────────────────┘
```

### render.py

- HTML 模板字符串 + **内联 CSS**（邮件客户端不支持外部样式表），把 Qwen 的 JSON 填入。
- 内联样式做基本排版：分组标题加粗分隔、条目间留白、链接可点、移动端可读。
- 同时生成**纯文本备份版**（`multipart/alternative`），不支持 HTML 的客户端也能读。
- 邮件主题：`AI 技术热点日报 · YYYY-MM-DD（共 N 条）`。

### mailer.py

- 标准库 `smtplib` + `email.mime`，无需第三方依赖。
- 配置走环境变量：`SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` / `MAIL_FROM` / `MAIL_TO`。
- 默认 SSL（465 端口），兼容 QQ/163/Gmail 等主流邮箱。
- 发送失败抛异常 → 整体失败 → 不写 seen.json → Actions 标红。

## 7. 配置、调度与项目结构

### 项目结构

```
hotspot-github/
├─ main.py                  # 入口：串起整个管道
├─ config.py                # 读环境变量，集中配置
├─ models.py                # Item 数据结构定义
├─ sources/
│  ├─ __init__.py           # 抓取器注册列表
│  ├─ base.py               # 抓取器接口 + 通用工具(URL规范化)
│  ├─ rss.py
│  ├─ hackernews.py
│  └─ github_trending.py
├─ pipeline.py              # 编排：抓取→去重→过滤已推送
├─ summarizer.py            # 调用 Qwen，输出结构化摘要
├─ render.py                # JSON → HTML + 纯文本邮件
├─ mailer.py                # SMTP 发送
├─ state.py                 # 读写 seen.json + 清理过期
├─ state/
│  └─ seen.json             # 已推送记录（仓库内持久化）
├─ requirements.txt         # feedparser, requests, openai, beautifulsoup4
├─ .env.example             # 配置样例（不含真实密钥）
├─ README.md                # 使用说明
└─ .github/workflows/
   └─ daily.yml             # 每日 9:30 定时工作流
```

### 配置项（环境变量 / GitHub Secrets）

| 变量 | 用途 |
|------|------|
| `DASHSCOPE_API_KEY` | 通义千问 API 密钥 |
| `QWEN_MODEL` | 模型名，默认 `qwen-plus` |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` | 邮件服务器与凭证 |
| `MAIL_FROM` / `MAIL_TO` | 发件人 / 收件人 |
| `ITEMS_PER_SOURCE` | 每源取几条，默认 10 |
| `AI_KEYWORDS` | AI 相关性初筛关键词（有默认值） |
| `RSS_FEEDS` | RSS 源 URL 列表（有默认值） |

### GitHub Actions 工作流（daily.yml）

- **触发**：`schedule: cron '30 1 * * *'`（UTC 01:30 = 北京 09:30）+ `workflow_dispatch`（手动触发测试）。
- **权限**：`contents: write`（commit 回 seen.json）。
- **步骤**：checkout → 装 Python 依赖 → 运行 `main.py`（密钥从 Secrets 注入）→ 若 seen.json 有变更则 commit & push。
- **注意**：GitHub cron 高峰期可能延迟几分钟到十几分钟，9:30 是"大约"而非精确。已接受。

### 本地开发

`.env` 文件 + `python main.py` 即可跑，方便调试。

## 8. 依赖

- `feedparser` — RSS/Atom 解析
- `requests` — HTTP 请求（HN API、GitHub Trending 页面）
- `openai` — 通义千问 OpenAI 兼容 SDK
- `beautifulsoup4` — 解析 GitHub Trending 页面 HTML
- 标准库 `smtplib` / `email` — 邮件发送（无需第三方）

## 9. 错误处理策略汇总

| 环节 | 失败处理 | 是否写状态 |
|------|---------|-----------|
| 单个抓取源 | 记日志、跳过、返回空列表 | 不影响 |
| 所有源都为空 | 记日志，跳过发信（无内容不发空邮件） | 不写 |
| Qwen 调用/JSON 解析 | 抛异常，整体失败 | 不写（下次重试） |
| SMTP 发送 | 抛异常，整体失败 | 不写（下次重试） |
| 发送成功 | — | 写入 seen.json + commit |
