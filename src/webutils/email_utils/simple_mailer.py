import re
import email
import imaplib
import smtplib
import socket
from email.message import EmailMessage
from typing import List, Optional


class SimpleMailer:
    """
    A simple email client for sending messages via SMTP and fetching messages via IMAP,
    with input validation and error handling.
    """

    EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        imap_server: str,
        email_address: str,
        password: str,
    ) -> None:
        """
        Initialize SMTP and IMAP connection parameters with validation.

        Args:
            smtp_server: Hostname of the SMTP server.
            smtp_port: Port of the SMTP server.
            imap_server: Hostname of the IMAP server.
            email_address: Email address to authenticate as.
            password: Password for the email account.

        Raises:
            TypeError: If any parameter is of incorrect type.
            ValueError: If any parameter is invalid (e.g., empty or malformed email).
        """
        # Validate types
        if not isinstance(smtp_server, str) or not smtp_server.strip():
            raise ValueError(f"Invalid SMTP server: '{smtp_server}'")
        if not isinstance(smtp_port, int) or smtp_port <= 0:
            raise ValueError(f"Invalid SMTP port: '{smtp_port}'")
        if not isinstance(imap_server, str) or not imap_server.strip():
            raise ValueError(f"Invalid IMAP server: '{imap_server}'")
        if not isinstance(email_address, str) or not self.EMAIL_PATTERN.match(email_address):
            raise ValueError(f"Invalid email address: '{email_address}'")
        if not isinstance(password, str) or not password:
            raise ValueError("Password must be a non-empty string.")

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

        Raises:
            ConnectionError: If unable to resolve host, connect, or authenticate.
        """
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
            server.starttls()
            server.login(self.email_address, self.password)
            return server
        except socket.gaierror as e:
            raise ConnectionError(f"SMTP server address resolution failed: {e}")
        except smtplib.SMTPAuthenticationError as e:
            raise ConnectionError(f"SMTP authentication failed: {e}")
        except (smtplib.SMTPException, OSError) as e:
            raise ConnectionError(f"SMTP connection failed: {e}")

    def _connect_imap(self) -> imaplib.IMAP4_SSL:
        """
        Create and return an authenticated IMAP SSL connection.

        Returns:
            An authenticated `imaplib.IMAP4_SSL` instance.

        Raises:
            ConnectionError: If unable to resolve host, connect, or authenticate.
        """
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_address, self.password)
            return mail
        except socket.gaierror as e:
            raise ConnectionError(f"IMAP server address resolution failed: {e}")
        except imaplib.IMAP4.error as e:
            raise ConnectionError(f"IMAP authentication failed: {e}")
        except OSError as e:
            raise ConnectionError(f"IMAP connection failed: {e}")

    def send_email(self, to_address: str, subject: str, body: str) -> None:
        """
        Send an email after validating inputs.

        Args:
            to_address: Recipient email address.
            subject: Email subject line.
            body: Plain-text body of the email.

        Raises:
            ValueError: If inputs are invalid.
            RuntimeError: If sending fails.
        """
        # Validate inputs
        if not isinstance(to_address, str) or not self.EMAIL_PATTERN.match(to_address):
            raise ValueError(f"Invalid recipient address: '{to_address}'")
        if not isinstance(subject, str):
            raise TypeError("Subject must be a string.")
        if not isinstance(body, str):
            raise TypeError("Body must be a string.")

        msg = EmailMessage()
        msg["From"] = self.email_address
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.set_content(body)

        try:
            with self._connect_smtp() as server:
                server.send_message(msg)
        except ConnectionError as e:
            # Preserve specific connection errors
            raise RuntimeError(f"Failed to send email: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error when sending email: {e}")

    def fetch_latest_emails(self, mailbox: str = "INBOX", limit: int = 5) -> List[str]:
        """
        Fetch the latest emails from a mailbox after validating inputs.

        Args:
            mailbox: Name of the mailbox (default is "INBOX").
            limit: Maximum number of messages to retrieve.

        Returns:
            A list of formatted email strings.

        Raises:
            ValueError: If inputs are invalid.
            RuntimeError: If fetching fails.
        """
        # Validate inputs
        if not isinstance(mailbox, str) or not mailbox.strip():
            raise ValueError(f"Invalid mailbox name: '{mailbox}'")
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError(f"Limit must be a positive integer, got: {limit}")

        messages: List[str] = []

        try:
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
        except ConnectionError as e:
            raise RuntimeError(f"Failed to fetch emails: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error when fetching emails: {e}")

        return messages
