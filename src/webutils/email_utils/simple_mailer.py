import re
import email
import imaplib
import smtplib
import socket
import base64
from email.header import decode_header, make_header
from email.message import EmailMessage
from typing import List, Optional


class SimpleMailer:
    """Simple SMTP/IMAP client with optional OAuth2 support."""

    EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        imap_server: str,
        email_address: str,
        password: Optional[str] = None,
        oauth2_token: Optional[str] = None,
        use_ssl: bool = False,
    ) -> None:
        """
        Initialize the mailer with SMTP and IMAP server info and authentication.

        Args:
            smtp_server: SMTP server hostname.
            smtp_port: SMTP server port.
            imap_server: IMAP server hostname.
            email_address: Email address for authentication.
            password: Account password for basic auth.
            oauth2_token: OAuth2 bearer token for XOAUTH2.
            use_ssl: If True, use SSL-wrapped SMTP; else STARTTLS.

        Raises:
            ValueError: On invalid parameters.
            TypeError: If use_ssl is not a bool.
        """
        if not isinstance(smtp_server, str) or not smtp_server.strip():
            raise ValueError("Invalid SMTP server")
        if not isinstance(smtp_port, int) or smtp_port <= 0:
            raise ValueError("Invalid SMTP port")
        if not isinstance(imap_server, str) or not imap_server.strip():
            raise ValueError("Invalid IMAP server")
        if not isinstance(email_address, str) or not self.EMAIL_PATTERN.match(email_address):
            raise ValueError("Invalid email address")
        if (password and oauth2_token) or (not password and not oauth2_token):
            raise ValueError("Provide exactly one of 'password' or 'oauth2_token'")
        if password is not None and not password:
            raise ValueError("Password must be non-empty")
        if oauth2_token is not None and not oauth2_token:
            raise ValueError("OAuth2 token must be non-empty")
        if not isinstance(use_ssl, bool):
            raise TypeError("use_ssl must be bool")

        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.imap_server = imap_server
        self.email_address = email_address
        self.password = password
        self.oauth2_token = oauth2_token
        self.use_ssl = use_ssl

    def _connect_smtp(self) -> smtplib.SMTP:
        """
        Establish and authenticate an SMTP connection.

        Returns:
            An authenticated smtplib.SMTP instance.

        Raises:
            ConnectionError: On connection or authentication failure.
        """
        try:
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
                server.ehlo()
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.ehlo()
                server.starttls()
                server.ehlo()

            if self.oauth2_token:
                auth_str = f"user={self.email_address}\x01auth=Bearer {self.oauth2_token}\x01\x01"
                auth_b64 = base64.b64encode(auth_str.encode()).decode('ascii')
                code, resp = server.docmd('AUTH', 'XOAUTH2 ' + auth_b64)
                if code != 235:
                    raise ConnectionError(f"SMTP OAuth2 auth failed: {code} {resp}")
            else:
                server.login(self.email_address, self.password)
            return server
        except (socket.gaierror, smtplib.SMTPException, OSError) as e:
            raise ConnectionError(f"SMTP connection/auth failed: {e}")

    def _connect_imap(self) -> imaplib.IMAP4_SSL:
        """
        Establish and authenticate an IMAP SSL connection.

        Returns:
            An authenticated IMAP4_SSL instance.

        Raises:
            ConnectionError: On connection or authentication failure.
        """
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            if self.oauth2_token:
                auth_str = f"user={self.email_address}\x01auth=Bearer {self.oauth2_token}\x01\x01"
                mail.authenticate('XOAUTH2', lambda _: auth_str.encode())
            else:
                mail.login(self.email_address, self.password)
            return mail
        except (socket.gaierror, imaplib.IMAP4.error, OSError) as e:
            raise ConnectionError(f"IMAP connection/auth failed: {e}")

    def send_email(self, to_address: str, subject: str, body: str) -> None:
        """
        Send a plain-text email.

        Args:
            to_address: Recipient email address.
            subject: Subject line.
            body: Text body of the email.

        Raises:
            ValueError: On invalid recipient address.
            RuntimeError: On send failure.
        """
        if not self.EMAIL_PATTERN.match(to_address):
            raise ValueError("Invalid recipient address")
        msg = EmailMessage()
        msg['From'] = self.email_address
        msg['To'] = to_address
        msg['Subject'] = subject
        msg.set_content(body)
        try:
            with self._connect_smtp() as server:
                server.send_message(msg)
        except ConnectionError as e:
            raise RuntimeError(f"Failed to send email: {e}")

    def _decode_header(self, raw: str) -> str:
        """
        Decode an RFC 2047 encoded header into a Unicode string.

        Args:
            raw: The raw header value.

        Returns:
            Decoded Unicode string.
        """
        try:
            return str(make_header(decode_header(raw)))
        except Exception:
            return raw

    def fetch_latest_emails(self, mailbox: str = 'INBOX', limit: int = 10) -> List[str]:
        """
        Fetch the latest messages from a mailbox.

        Args:
            mailbox: Mailbox name (e.g., 'INBOX').
            limit: Number of emails to retrieve.

        Returns:
            A list of formatted strings: "From: ...\nSubject: ...\n\n<body>".

        Raises:
            ValueError: On invalid arguments.
            RuntimeError: On fetch failure.
        """
        if not isinstance(mailbox, str) or not mailbox:
            raise ValueError("Mailbox must be a non-empty string")
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("Limit must be a positive integer")

        try:
            mail = self._connect_imap()
            status, _ = mail.select(mailbox)
            if status != 'OK':
                mail.logout()
                return []

            status, data = mail.search(None, 'ALL')
            if status != 'OK' or not data:
                mail.logout()
                return []

            uids = data[0].split()[-limit:]
            messages: List[str] = []
            for uid in reversed(uids):
                status, msg_data = mail.fetch(uid, '(RFC822)')
                if status != 'OK' or not msg_data:
                    continue

                raw = msg_data[0][1]
                m = email.message_from_bytes(raw)
                sender = self._decode_header(m.get('From', ''))
                subject = self._decode_header(m.get('Subject', ''))

                body = ''
                if m.is_multipart():
                    for part in m.walk():
                        if part.get_content_type() == 'text/plain' and not part.is_multipart():
                            body = part.get_payload(decode=True).decode(
                                part.get_content_charset() or 'utf-8',
                                errors='replace'
                            )
                            break
                else:
                    body = m.get_payload(decode=True).decode(
                        m.get_content_charset() or 'utf-8',
                        errors='replace'
                    )

                messages.append(f"From: {sender}\nSubject: {subject}\n\n{body.strip()}")
            mail.logout()
            return messages
        except ConnectionError as e:
            raise RuntimeError(f"Failed to fetch emails: {e}")
