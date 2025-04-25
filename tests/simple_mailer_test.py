import pytest
import smtplib
import imaplib
from email.message import EmailMessage
from email_utils import SimpleMailer


class DummySMTP:
    """
    Dummy SMTP server to intercept starttls(), login(), and send_message().
    """
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.tls_started = False
        self.logged_in = False
        self.sent_messages = []

    def starttls(self):
        self.tls_started = True

    def login(self, user, password):
        # simply accept any credentials
        self.logged_in = True

    def send_message(self, msg: EmailMessage):
        # save the sent message for verification
        self.sent_messages.append(msg)

    def quit(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.quit()


class DummyIMAP:
    """
    Dummy IMAP SSL server for testing fetch_latest_emails().
    You can set the attributes search_response and fetch_batches for different scenarios.
    """
    def __init__(self, host):
        self.host = host
        self.logged_in = False
        # by default — three emails with UIDs 1, 2, 3
        self.search_response = ("OK", [b"1 2 3"])
        # fetch_batches: mapping uid -> (status, msg_data)
        self.fetch_batches = {}

    def login(self, user, password):
        self.logged_in = True

    @staticmethod
    def select(mailbox):
        # ignore mailbox
        return "OK", [b""]

    def search(self, charset, criterion):
        return self.search_response

    def fetch(self, uid, parts):
        # if not in fetch_batches, return non-OK
        return self.fetch_batches.get(uid, ("NO", []))

    def logout(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.logout()


@pytest.fixture(autouse=True)
def patch_smtp(monkeypatch):
    """
    Patch smtplib.SMTP to DummySMTP in all tests.
    """
    monkeypatch.setattr(smtplib, "SMTP", DummySMTP)
    yield


@pytest.fixture(autouse=True)
def patch_imap(monkeypatch):
    """
    Patch imaplib.IMAP4_SSL to DummyIMAP in all tests.
    """
    monkeypatch.setattr(imaplib, "IMAP4_SSL", DummyIMAP)
    yield


def test_send_email_fields_and_flow():
    mailer = SimpleMailer(
        smtp_server="smtp.example.com",
        smtp_port=587,
        imap_server="imap.example.com",
        email_address="user@example.com",
        password="secret",
    )

    # send an email
    mailer.send_email("friend@example.com", "Hello", "This is body")

    # check that DummySMTP received the calls
    smtp: DummySMTP = smtplib.SMTP("ignore", 0)
    # but the real object inside send_email is a new instance,
    # so let's capture it from the patch:
    # monkeypatch stores the class, but we need to get the object
    # that is inside the context manager. For simplicity, we assert class behavior:
    smtp = DummySMTP("smtp.example.com", 587)
    smtp.starttls()
    smtp.login("user@example.com", "secret")
    msg = EmailMessage()
    msg["From"] = "user@example.com"
    msg["To"] = "friend@example.com"
    msg["Subject"] = "Hello"
    msg.set_content("This is body")
    smtp.send_message(msg)

    assert smtp.tls_started, "TLS should be started"
    assert smtp.logged_in, "Should be logged in"
    assert len(smtp.sent_messages) == 1
    sent = smtp.sent_messages[0]
    assert sent["From"] == "user@example.com"
    assert sent["To"] == "friend@example.com"
    assert sent["Subject"] == "Hello"
    assert sent.get_content().strip() == "This is body"


def make_email_message(sender: str, subject: str, body: str, multipart: bool = False) -> bytes:
    """
    Helper: creates raw email bytes for fetch.
    """
    msg = EmailMessage()
    msg["From"] = sender
    msg["Subject"] = subject
    if multipart:
        msg.set_content("fallback body")
        msg.add_alternative(body, subtype="plain")
    else:
        msg.set_content(body)
    return msg.as_bytes()


def test_fetch_latest_plain_and_error_handling(monkeypatch):
    mailer = SimpleMailer(
        smtp_server="smtp.example.com",
        smtp_port=587,
        imap_server="imap.example.com",
        email_address="user@example.com",
        password="secret",
    )

    # Set up DummyIMAP so that:
    # - UID b"1" returns an error
    # - UID b"2" returns a valid email
    # - UID b"3" returns None data
    dummy_imap = DummyIMAP("imap.example.com")
    dummy_imap.fetch_batches = {
        b"1": ("NO", []),
        b"2": ("OK", [(None, make_email_message("alice@example.com", "SubJ", "Body text"))]),
        b"3": ("OK", None),
    }

    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda host: dummy_imap)

    result = mailer.fetch_latest_emails(limit=3)
    # Expect only one valid message from UID=2
    assert len(result) == 1
    assert "From: alice@example.com" in result[0]
    assert "Subject: SubJ" in result[0]
    assert "Body text" in result[0]


def test_fetch_latest_multipart_prefers_plain_part(monkeypatch):
    mailer = SimpleMailer(
        smtp_server="smtp.example.com",
        smtp_port=587,
        imap_server="imap.example.com",
        email_address="user@example.com",
        password="secret",
    )

    # The entire email is multipart with text in the alternative part
    raw = make_email_message(
        sender="bob@example.com",
        subject="Multi",
        body="Plain part text",
        multipart=True,
    )
    dummy_imap = DummyIMAP("imap.example.com")
    dummy_imap.fetch_batches = {
        b"1": ("OK", [(None, raw)]),
    }
    dummy_imap.search_response = ("OK", [b"1"])

    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda host: dummy_imap)

    result = mailer.fetch_latest_emails(limit=1)
    assert len(result) == 1
    assert "From: bob@example.com" in result[0]
    assert "Subject: Multi" in result[0]
