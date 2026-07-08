import mailer


def test_build_message_sets_headers_and_both_parts():
    msg = mailer.build_message(
        subject="测试主题",
        html="<body>你好 HTML</body>",
        text="你好 纯文本",
        mail_from="from@x.com",
        mail_to="to@y.com",
    )
    assert msg["Subject"] == "测试主题"
    assert msg["From"] == "from@x.com"
    assert msg["To"] == "to@y.com"
    assert msg.get_content_type() == "multipart/alternative"

    payloads = msg.get_payload()
    types = {p.get_content_type() for p in payloads}
    assert types == {"text/plain", "text/html"}
    # 纯文本在前，HTML 在后（alternative 约定：优先展示最后一个）
    assert payloads[0].get_content_type() == "text/plain"
    assert payloads[1].get_content_type() == "text/html"


class FakeSMTP:
    instances = []

    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port
        self.logged_in = None
        self.sent = None
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def login(self, user, password):
        self.logged_in = (user, password)

    def send_message(self, msg, to_addrs=None):
        self.sent = msg
        self.to_addrs = to_addrs


def test_parse_recipients_single():
    assert mailer.parse_recipients("a@x.com") == ["a@x.com"]


def test_parse_recipients_multiple_with_spaces():
    assert mailer.parse_recipients("a@x.com, b@y.com ,c@z.com") == [
        "a@x.com", "b@y.com", "c@z.com",
    ]


def test_parse_recipients_ignores_empty_segments():
    assert mailer.parse_recipients("a@x.com,,b@y.com,") == ["a@x.com", "b@y.com"]


def test_send_logs_in_and_sends(monkeypatch):
    FakeSMTP.instances = []
    monkeypatch.setattr(mailer.smtplib, "SMTP_SSL", FakeSMTP)

    mailer.send(
        subject="s", html="<body>h</body>", text="t",
        host="smtp.x.com", port=465,
        user="u@x.com", password="secret",
        mail_from="u@x.com", mail_to="to@y.com",
    )

    assert len(FakeSMTP.instances) == 1
    smtp = FakeSMTP.instances[0]
    assert smtp.host == "smtp.x.com"
    assert smtp.port == 465
    assert smtp.logged_in == ("u@x.com", "secret")
    assert smtp.sent["Subject"] == "s"
    assert smtp.sent["To"] == "to@y.com"


def test_send_to_multiple_recipients(monkeypatch):
    FakeSMTP.instances = []
    monkeypatch.setattr(mailer.smtplib, "SMTP_SSL", FakeSMTP)

    mailer.send(
        subject="s", html="<body>h</body>", text="t",
        host="smtp.x.com", port=465,
        user="u@x.com", password="secret",
        mail_from="u@x.com", mail_to="a@x.com, b@y.com,c@z.com",
    )

    smtp = FakeSMTP.instances[0]
    # To 头显示全部收件人
    assert smtp.sent["To"] == "a@x.com, b@y.com, c@z.com"
    # 实际投递地址是拆分后的列表，确保每个人都收到
    assert smtp.to_addrs == ["a@x.com", "b@y.com", "c@z.com"]


def test_send_propagates_smtp_error(monkeypatch):
    class BoomSMTP(FakeSMTP):
        def send_message(self, msg, to_addrs=None):
            raise RuntimeError("smtp refused")

    monkeypatch.setattr(mailer.smtplib, "SMTP_SSL", BoomSMTP)
    try:
        mailer.send(
            subject="s", html="h", text="t",
            host="smtp.x.com", port=465,
            user="u", password="p",
            mail_from="u@x.com", mail_to="to@y.com",
        )
        assert False, "expected error to propagate"
    except RuntimeError as exc:
        assert "smtp refused" in str(exc)
