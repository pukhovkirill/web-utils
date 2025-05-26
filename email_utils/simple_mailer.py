import email
import imaplib
import smtplib
from email.message import EmailMessage
from typing import List, Optional


class SimpleMailer:
    """
    A simple email client for sending messages via SMTP and fetching messages via IMAP.
    """

    def __init__(
            self,
            smtp_server: str,
            smtp_port: int,
            imap_server: str,
            email_address: str,
            password: str,
    ) -> None:
        """
        Initialize SMTP and IMAP connection parameters.

        Args:
            smtp_server: Hostname of the SMTP server.
            smtp_port: Port of the SMTP server.
            imap_server: Hostname of the IMAP server.
            email_address: Email address to authenticate as.
            password: Password for the email account.

        Returns:
            None
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.imap_server = imap_server
        self.email_address = email_address
        self.password = password

    def _connect_smtp(self) -> smtplib.SMTP:
        """
        Create and return an authenticated SMTP connection.

        Returns:
            An authenticated `smtplib.SMTP` instance with TLS enabled.
        """
        server = smtplib.SMTP(self.smtp_server, self.smtp_port)
        server.starttls()
        server.login(self.email_address, self.password)
        return server

    def _connect_imap(self) -> imaplib.IMAP4_SSL:
        """
        Create and return an authenticated IMAP SSL connection.

        Returns:
            An authenticated `imaplib.IMAP4_SSL` instance.
        """
        mail = imaplib.IMAP4_SSL(self.imap_server)
        mail.login(self.email_address, self.password)
        return mail

    def send_email(self, to_address: str, subject: str, body: str) -> None:
        """
        Send an email.

        Args:
            to_address: Recipient email address.
            subject: Email subject line.
            body: Plain-text body of the email.

        Returns:
            None
        """
        msg = EmailMessage()
        msg["From"] = self.email_address
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.set_content(body)

        with self._connect_smtp() as server:
            server.send_message(msg)

    def fetch_latest_emails(self, mailbox: str = "INBOX", limit: int = 5) -> List[str]:
        """
        Fetch the latest emails from a mailbox.

        Args:
            mailbox: Name of the mailbox (default is "INBOX").
            limit: Maximum number of messages to retrieve.

        Returns:
            A list of formatted email strings in the format:
            "From: <sender>\nSubject: <subject>\n\n<body>"
        """
        messages: List[str] = []

        with self._connect_imap() as mail:
            mail.select(mailbox)

            status, data = mail.search(None, "ALL")
            if status != "OK" or not data:
                return []

            uids = data[0].split()[-limit:]

            for uid in reversed(uids):
                status, msg_data = mail.fetch(uid, "(RFC822)")

                if status != "OK" or not msg_data:
                    continue

                first_part = msg_data[0]
                if (
                        not isinstance(first_part, tuple)
                        or len(first_part) < 2
                        or not isinstance(first_part[1], (bytes, bytearray))
                ):
                    continue

                raw_email = first_part[1]
                msg = email.message_from_bytes(raw_email)

                subject = msg.get("Subject", "(No Subject)")
                sender = msg.get("From", "(Unknown)")
                body: Optional[str] = None

                if msg.is_multipart():
                    for part in msg.walk():
                        if (
                                part.get_content_type() == "text/plain"
                                and not part.get("Content-Disposition")
                        ):
                            charset = part.get_content_charset() or "utf-8"
                            body = part.get_payload(decode=True).decode(
                                charset, errors="replace"
                            )
                            break
                else:
                    charset = msg.get_content_charset() or "utf-8"
                    body = msg.get_payload(decode=True).decode(
                        charset, errors="replace"
                    )

                body_text = body.strip() if body else ""
                formatted = f"From: {sender}\nSubject: {subject}\n\n{body_text}"
                messages.append(formatted)

        return messages
