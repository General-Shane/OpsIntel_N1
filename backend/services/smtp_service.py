import os
import re
import ssl
import smtplib
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formataddr
from typing import Optional, List, Dict, Any, Tuple
from email_validator import validate_email, EmailNotValidError
import structlog

from backend.config import settings

logger = structlog.get_logger(__name__)

def sanitize_header(val: Optional[str]) -> str:
    """
    Prevents CRLF and header injection by stripping carriage returns, newlines,
    null bytes, and control characters.
    """
    if not val:
        return ""
    # Strip any \r, \n, null bytes, and control chars
    clean = re.sub(r'[\r\n\x00-\x1f\x7f]', ' ', str(val))
    return clean.strip()


def validate_and_normalize_email(email_str: str) -> str:
    """
    Validates an email address against RFC standards and ensures no CRLF injection.
    Supports enterprise intranet domains (.local, .internal, .corp) and test environments.
    Raises ValueError on invalid format or header injection attempt.
    """
    if not email_str:
        raise ValueError("Email address cannot be empty.")
    
    clean_email = sanitize_header(email_str).strip()
    if any(char in email_str for char in ('\r', '\n', '\x00')):
        raise ValueError(f"CRLF or control character injection detected in email address: '{email_str}'")

    # Basic RFC syntax check
    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', clean_email):
        raise ValueError(f"Invalid email address format: '{email_str}'")

    try:
        valid = validate_email(clean_email, check_deliverability=False, test_environment=True)
        return valid.normalized
    except EmailNotValidError as exc:
        # Allow enterprise intranet / mock domains if format is valid
        if re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', clean_email):
            return clean_email.lower()
        raise ValueError(f"Invalid email address '{email_str}': {str(exc)}") from exc


def mask_smtp_host(host: Optional[str]) -> str:
    """Safely masks SMTP server host for UI presentation and logs."""
    if not host:
        return "Not Configured"
    parts = host.split(".")
    if len(parts) >= 2:
        return f"{parts[0][:3]}***.{'.'.join(parts[1:])}"
    return f"{host[:3]}***"


class SMTPService:
    """
    Enterprise SMTP/TLS transport for transactional and scheduled report dispatches.
    Features:
      - STARTTLS and implicit SSL/TLS support with SSL context verification
      - Strict CRLF and email header injection protection
      - Multi-part plain text + HTML email formatting with Capgemini executive styling
      - Binary MIME attachments (PDF executive operations documents)
      - Mock mode for automated testing without live mail servers
      - Zero credential logging or exposure
    """
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        use_tls: Optional[bool] = None,
        use_ssl: Optional[bool] = None,
        timeout: Optional[float] = None,
        mock_mode: Optional[bool] = None
    ):
        self.host = host if host is not None else settings.SMTP_HOST
        self.port = port if port is not None else settings.SMTP_PORT
        self.username = username if username is not None else settings.SMTP_USERNAME
        self.password = password if password is not None else settings.SMTP_PASSWORD
        self.from_email = from_email if from_email is not None else settings.SMTP_FROM
        self.from_name = sanitize_header(from_name if from_name is not None else settings.SMTP_FROM_NAME)
        self.use_tls = use_tls if use_tls is not None else settings.SMTP_USE_TLS
        self.use_ssl = use_ssl if use_ssl is not None else settings.SMTP_USE_SSL
        self.timeout = timeout if timeout is not None else settings.SMTP_TIMEOUT_SECONDS
        self.mock_mode = mock_mode if mock_mode is not None else settings.SMTP_MOCK_MODE

        # In-memory sent email history for testing & verification
        self._sent_mailbox: List[Dict[str, Any]] = []

    @property
    def is_configured(self) -> bool:
        """Determines if sufficient configuration exists for outbound email dispatch."""
        if self.mock_mode:
            return True
        return bool(self.host and self.port and self.from_email)

    def get_status_summary(self) -> Dict[str, Any]:
        """Returns safe, non-sensitive configuration metadata for UI and status endpoints."""
        return {
            "is_configured": self.is_configured,
            "mock_mode": self.mock_mode,
            "host_masked": mask_smtp_host(self.host) if self.host else "Not Configured",
            "port": self.port,
            "username_configured": bool(self.username),
            "from_email": self.from_email,
            "from_name": self.from_name,
            "use_tls": self.use_tls,
            "use_ssl": self.use_ssl,
            "timeout_seconds": self.timeout
        }

    def build_mime_message(
        self,
        recipients: List[str],
        subject: str,
        text_body: str,
        html_body: Optional[str] = None,
        attachment_path: Optional[str] = None,
        attachment_filename: Optional[str] = None
    ) -> Tuple[MIMEMultipart, List[str]]:
        """
        Constructs a sanitized, multi-part MIME message.
        Validates all recipients and sanitizes headers.
        """
        # Validate recipients
        validated_recipients = []
        for r in recipients:
            norm = validate_and_normalize_email(r)
            if norm not in validated_recipients:
                validated_recipients.append(norm)

        if not validated_recipients:
            raise ValueError("No valid recipients provided.")

        clean_subject = sanitize_header(subject)
        if not clean_subject:
            clean_subject = "OPSINTEL Operations Notification"

        clean_from_email = validate_and_normalize_email(self.from_email)
        from_header = formataddr((self.from_name, clean_from_email)) if self.from_name else clean_from_email

        # Root multipart container
        if attachment_path:
            msg = MIMEMultipart("mixed")
            body_container = MIMEMultipart("alternative")
            msg.attach(body_container)
        else:
            msg = MIMEMultipart("alternative")
            body_container = msg

        msg["From"] = from_header
        msg["To"] = ", ".join(validated_recipients)
        msg["Subject"] = clean_subject
        msg["X-Mailer"] = "OPSINTEL Enterprise Operations Mailer"

        # Plain-text part
        body_container.attach(MIMEText(text_body, "plain", "utf-8"))

        # HTML part
        if html_body:
            body_container.attach(MIMEText(html_body, "html", "utf-8"))

        # PDF or file attachment
        if attachment_path and os.path.exists(attachment_path):
            filename = attachment_filename or os.path.basename(attachment_path)
            clean_filename = sanitize_header(filename)
            with open(attachment_path, "rb") as f:
                file_bytes = f.read()
            
            part = MIMEApplication(file_bytes, Name=clean_filename)
            part["Content-Disposition"] = f'attachment; filename="{clean_filename}"'
            msg.attach(part)

        return msg, validated_recipients

    def send_email(
        self,
        recipients: List[str],
        subject: str,
        text_body: str,
        html_body: Optional[str] = None,
        attachment_path: Optional[str] = None,
        attachment_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends an email message via real SMTP/TLS or records to mock mailbox.
        Returns delivery result summary or raises Exception on failure.
        """
        msg, valid_recipients = self.build_mime_message(
            recipients=recipients,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            attachment_path=attachment_path,
            attachment_filename=attachment_filename
        )

        clean_from_email = validate_and_normalize_email(self.from_email)

        # 1. Mock Transport Mode
        if self.mock_mode or not self.host:
            record = {
                "from": clean_from_email,
                "recipients": valid_recipients,
                "subject": msg["Subject"],
                "text_body": text_body,
                "has_html": bool(html_body),
                "has_attachment": bool(attachment_path),
                "attachment_filename": attachment_filename or (os.path.basename(attachment_path) if attachment_path else None),
                "status": "SENT_MOCK"
            }
            self._sent_mailbox.append(record)
            logger.info(
                "mock_email_dispatched",
                recipients=valid_recipients,
                subject=msg["Subject"],
                has_attachment=bool(attachment_path)
            )
            return {
                "status": "SENT",
                "mode": "MOCK",
                "recipients": valid_recipients,
                "subject": msg["Subject"],
                "provider_message_id": f"mock-msg-{len(self._sent_mailbox)}"
            }

        # 2. Live SMTP Transport Mode
        server = None
        try:
            if self.use_ssl:
                ssl_context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=self.timeout, context=ssl_context)
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=self.timeout)

            server.ehlo()

            if self.use_tls and not self.use_ssl:
                ssl_context = ssl.create_default_context()
                server.starttls(context=ssl_context)
                server.ehlo()

            if self.username and self.password:
                server.login(self.username, self.password)

            server.send_message(msg, from_addr=clean_from_email, to_addrs=valid_recipients)
            
            logger.info(
                "smtp_email_dispatched",
                recipients=valid_recipients,
                subject=msg["Subject"],
                host=self.host,
                port=self.port
            )
            return {
                "status": "SENT",
                "mode": "SMTP",
                "recipients": valid_recipients,
                "subject": msg["Subject"],
                "provider_message_id": f"smtp-{self.host}-{msg.get('Message-ID', 'ok')}"
            }
        except smtplib.SMTPAuthenticationError as auth_err:
            logger.error("smtp_authentication_failed", host=self.host, code=auth_err.smtp_code)
            raise RuntimeError(f"SMTP authentication failed (Code {auth_err.smtp_code})") from auth_err
        except smtplib.SMTPResponseException as resp_err:
            logger.error("smtp_response_error", host=self.host, code=resp_err.smtp_code, error=str(resp_err.smtp_error))
            raise RuntimeError(f"SMTP error {resp_err.smtp_code}: {resp_err.smtp_error}") from resp_err
        except Exception as exc:
            logger.error("smtp_connection_failed", host=self.host, error=str(exc))
            raise exc
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass

    def get_sent_messages(self) -> List[Dict[str, Any]]:
        """Returns the in-memory log of mock-dispatched messages for test verification."""
        return list(self._sent_mailbox)

    def clear_sent_messages(self):
        """Clears the mock mailbox."""
        self._sent_mailbox.clear()

# Global default instance
smtp_service = SMTPService()
