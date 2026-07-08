"""SMTP 邮件发送：标准库 smtplib + SSL，发送 HTML+纯文本双版本。"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def parse_recipients(mail_to: str) -> list[str]:
    """把逗号分隔的收件人字符串拆成列表，忽略空段与首尾空格。"""
    return [addr.strip() for addr in mail_to.split(",") if addr.strip()]


def build_message(
    subject: str, html: str, text: str, mail_from: str, mail_to: str
) -> MIMEMultipart:
    """构造 multipart/alternative 邮件：纯文本在前，HTML 在后。

    mail_to 可为单个邮箱或逗号分隔的多个邮箱；To 头统一规范化展示。
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = ", ".join(parse_recipients(mail_to))
    # alternative 约定：客户端优先展示最后一个可渲染的部分
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    return msg


def send(
    subject: str, html: str, text: str,
    host: str, port: int, user: str, password: str,
    mail_from: str, mail_to: str,
) -> None:
    """通过 SMTP over SSL 发送邮件。mail_to 支持逗号分隔的多收件人。任何失败向上抛出。"""
    message = build_message(subject, html, text, mail_from, mail_to)
    recipients = parse_recipients(mail_to)
    with smtplib.SMTP_SSL(host, port, timeout=30) as server:
        server.login(user, password)
        server.send_message(message, to_addrs=recipients)
    logger.info("邮件已发送至 %s", ", ".join(recipients))
