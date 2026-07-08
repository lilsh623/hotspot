# hotspot-github · AI 技术热点日报 Agent

每日北京时间约 9:30 自动抓取 AI/技术热点，用通义千问 Qwen 生成中文重点摘要，通过邮件推送。由 GitHub Actions 定时驱动，无需自建服务器。

## 工作流程

```
抓取(HackerNews + GitHub Trending + RSS) → 去重/剔除已推送 → Qwen 中文摘要 → 渲染 HTML 邮件 → SMTP 发送 → 记录已推送
```

- **多来源**：Hacker News（官方 API）、GitHub Trending（HTML 解析）、RSS/官方博客（OpenAI、Anthropic、Google AI、HuggingFace 等）
- **每源取数**：各取最热/最新 8-10 条（`ITEMS_PER_SOURCE`，默认 10）
- **摘要引擎**：通义千问 `qwen-plus`，只做翻译 + 摘要 + 写总览，不做筛选
- **邮件**：HTML + 纯文本双版本，顶部当日总览 + 按来源分组的条目列表
- **去重**：`state/seen.json` 记录已推送 URL，每条只推一次；自动清理 30 天前记录
- **可靠性**：单个抓取源失败自动跳过；只有邮件发送成功后才写状态（失败则下次重试）

## 本地运行

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env      # 填入你的 Qwen key 与 SMTP 配置
set -a && source .env && set +a
python main.py
```

## 部署到 GitHub Actions（推荐）

1. 把本仓库推到 GitHub。
2. 在 **Settings → Secrets and variables → Actions** 配置：

   **Secrets（密钥）**：
   `DASHSCOPE_API_KEY`、`SMTP_HOST`、`SMTP_PORT`、`SMTP_USER`、`SMTP_PASS`、`MAIL_FROM`、`MAIL_TO`

   **Variables（可选，非敏感）**：
   `QWEN_MODEL`（默认 `qwen-plus`）、`ITEMS_PER_SOURCE`（默认 `10`）

3. 工作流 `.github/workflows/daily.yml` 已配置每日 UTC 01:30（北京 09:30）触发，也可在 Actions 页面手动 **Run workflow** 测试。

> 注意：GitHub cron 在高峰期可能延迟几分钟到十几分钟，9:30 是“大约”而非精确时间。

## 配置项

| 变量 | 说明 | 默认 |
|------|------|------|
| `DASHSCOPE_API_KEY` | 通义千问 API 密钥（必填） | — |
| `QWEN_MODEL` | 模型名 | `qwen-plus` |
| `ITEMS_PER_SOURCE` | 每个来源抓取条数 | `10` |
| `AI_KEYWORDS` | AI 相关性初筛关键词（逗号分隔） | 内置一组 |
| `RSS_FEEDS` | RSS 源 URL 列表（逗号分隔） | 内置一组官方博客 |
| `SMTP_HOST/PORT/USER/PASS` | 邮件服务器与凭证（必填） | 端口默认 `465` |
| `MAIL_FROM` / `MAIL_TO` | 发件人 / 收件人（必填） | — |

## 扩展新的抓取源

1. 在 `sources/` 下新增一个模块，实现 `fetch(limit: int) -> list[Item]`（失败时内部捕获、返回空列表）。
2. 在 `sources/__init__.py` 的 `FETCHERS` 列表里注册它。

## 开发

```bash
pip install pytest
python -m pytest        # 运行全部单元测试
```

设计文档见 `docs/superpowers/specs/2026-07-08-ai-hotspot-agent-design.md`。
