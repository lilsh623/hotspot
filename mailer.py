"""SMTP 邮件发送：标准库 smtplib + SSL，发送 HTML+纯文本双版本。"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def build_message(
    subject: str, html: str, text: str, mail_from: str, mail_to: str
) -> MIMEMultipart:
    """构造 multipart/alternative 邮件：纯文本在前，HTML 在后。"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = mail_to
    # alternative 约定：客户端优先展示最后一个可渲染的部分
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    return msg


def send(
    subject: str, html: str, text: str,
    host: str, port: int, user: str, password: str,
    mail_from: str, mail_to: str,
) -> None:
    """通过 SMTP over SSL 发送邮件。任何失败向上抛出。"""
    message = build_message(subject, html, text, mail_from, mail_to)
    with smtplib.SMTP_SSL(host, port, timeout=30) as server:
        server.login(user, password)
        server.send_message(message)
    logger.info("邮件已发送至 %s", mail_to)
