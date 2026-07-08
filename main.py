"""AI 技术热点日报入口。

管道：抓取 → 去重/过滤已推送 → Qwen 摘要 → 渲染 → 发送 → 成功后写状态。
关键不变量：只有邮件发送成功后才写 seen.json（发送失败则不写，下次重试）。
"""

import logging
import sys
from datetime import date
from pathlib import Path

import config
import mailer
import pipeline
import render
import state
import summarizer
from sources import FETCHERS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("hotspot")

SEEN_PATH = Path(__file__).parent / "state" / "seen.json"


def run(
    fetchers,
    items_per_source: int,
    load_state,
    summarize,
    send,
    save_state,
    today: date,
) -> int:
    """编排整个流程。返回进程退出码（0 表示正常）。

    依赖以函数参数注入，便于测试：
      load_state() -> dict            读取已推送记录
      summarize(items) -> dict        Qwen 摘要，返回 {overview, items}
      send(subject, html, text)       发送邮件，失败抛异常
      save_state(dict)                写回已推送记录
    """
    seen = load_state()
    raw = pipeline.gather(fetchers, items_per_source)
    logger.info("抓取合计 %d 条", len(raw))

    candidates = pipeline.dedupe_and_filter(raw, state.seen_url_set(seen))
    logger.info("去重并剔除已推送后剩余 %d 条", len(candidates))

    if not candidates:
        logger.info("没有新内容，跳过发信。")
        return 0

    summary = summarize(candidates)
    subject = render.subject(len(summary.get("items", [])), today)
    html = render.render_html(summary)
    text = render.render_text(summary)

    send(subject, html, text)

    # 仅在发送成功后才走到这里：记录 + 清理过期
    pushed_urls = [it.url for it in candidates]
    updated = state.record(seen, pushed_urls, today=today)
    updated = state.prune(updated, today=today, days=30)
    save_state(updated)
    logger.info("已写入状态，本次推送 %d 条。", len(pushed_urls))
    return 0


def main() -> int:
    client = summarizer.make_client()

    def do_summarize(items):
        return summarizer.summarize(items, client=client, model=config.QWEN_MODEL)

    def do_send(subject, html, text):
        mailer.send(
            subject=subject, html=html, text=text,
            host=config.require("SMTP_HOST"), port=config.SMTP_PORT,
            user=config.require("SMTP_USER"), password=config.require("SMTP_PASS"),
            mail_from=config.require("MAIL_FROM"), mail_to=config.require("MAIL_TO"),
        )

    return run(
        fetchers=FETCHERS,
        items_per_source=config.ITEMS_PER_SOURCE,
        load_state=lambda: state.load(SEEN_PATH),
        summarize=do_summarize,
        send=do_send,
        save_state=lambda data: state.save(SEEN_PATH, data),
        today=date.today(),
    )


if __name__ == "__main__":
    sys.exit(main())
