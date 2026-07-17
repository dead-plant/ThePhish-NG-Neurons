#!/usr/bin/env python3
"""PhishMailer: Cortex responder that sends a TheHive case/task description via email.

Directive line inside the description (everything after it becomes the body):

    #PhishMailer; subject: "Optional subject" ;mailto:a@x.com; mailto: b@y.com;

Grammar: ';'-separated fields, whitespace around ';' and ':' is allowed,
the line MUST end with ';'. At most one subject:"..." (optional, quoted,
may contain ';'), one or more mailto: recipients. If no subject is given,
one is built as: TheHive Case/Task [id]: title.
"""

import re
import smtplib
import ssl
from collections.abc import Sequence
from email.message import EmailMessage
from email.policy import SMTP as SMTP_POLICY
from email.utils import formatdate, make_msgid, parseaddr
from typing import Literal, Optional

from cortexutils.responder import Responder
from email_validator import validate_email, EmailNotValidError

TLS_MODES = ("tls", "starttls", "none")
MAX_SUBJECT_LEN = 120
SUBJECT_TITLE_LIMIT = 60

MARKER = "#PhishMailer"
_MARKER_RE = re.compile(r'#PhishMailer\s*;')
_SUBJECT_FIELD_RE = re.compile(r'subject\s*:\s*"([^"]*)"')
_MAILTO_FIELD_RE = re.compile(r'mailto\s*:\s*(\S+)')


class NoRecipientFoundError(Exception):
    pass


class InvalidDirectiveError(Exception):
    pass


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def _split_fields(text: str):
    """Split on ';' that are outside double quotes."""
    fields, buf, in_quotes = [], [], False
    for ch in text:
        if ch == '"':
            in_quotes = not in_quotes
            buf.append(ch)
        elif ch == ';' and not in_quotes:
            fields.append(''.join(buf))
            buf = []
        else:
            buf.append(ch)
    if in_quotes:
        raise InvalidDirectiveError('Unterminated quote in subject.')
    fields.append(''.join(buf))  # remainder after the last ';'
    return fields


def extract_recipients(description_lines: Sequence[str]):
    """Parse the first marker line of a description.

    Returns (recipients, subject, start_index):
      recipients  - list of validated, normalized, deduplicated addresses
      subject     - the quoted subject (stripped), or None if not supplied
      start_index - index of the first body line (line after the marker)

    All directive validation happens here. Raises NoRecipientFoundError if
    no marker line exists, InvalidDirectiveError for a malformed directive,
    EmailNotValidError for an invalid recipient address.
    """
    for index, line in enumerate(description_lines):
        if not line.startswith(MARKER):
            continue

        stripped = line.rstrip()
        match = _MARKER_RE.match(stripped)
        if not match:
            raise InvalidDirectiveError(f"Expected ';' after {MARKER}.")
        if not stripped.endswith(';'):
            raise InvalidDirectiveError("Directive must end with ';'.")

        fields = _split_fields(stripped[match.end():])
        fields = fields[:-1]  # remainder after the final ';' is always empty

        subject = None
        recipients = []
        for field in fields:
            field = field.strip()
            if not field:
                continue
            if m := _SUBJECT_FIELD_RE.fullmatch(field):
                if subject is not None:
                    raise InvalidDirectiveError("More than one subject given.")
                subject = m.group(1).strip()
                if not subject:
                    raise InvalidDirectiveError("Subject must not be empty.")

                subject = _truncate(subject, MAX_SUBJECT_LEN)

            elif m := _MAILTO_FIELD_RE.fullmatch(field):
                valid = validate_email(m.group(1), check_deliverability=True)

                addr = getattr(valid, 'normalized', None)
                if addr not in recipients:  # dedupe, keep order
                    recipients.append(addr)
            else:
                raise InvalidDirectiveError(f"Unknown field: {field!r}")

        if not recipients:
            raise NoRecipientFoundError("No 'mailto:' recipient given.")
        return recipients, subject, index + 1

    raise InvalidDirectiveError("Got empty description.")


def send_email(
    *,
    from_addr: str,
    to_addrs: Sequence[str],
    subject: str,
    body_lines: Sequence[str],
    host: str,
    port: int,
    tls_mode: Literal["tls", "starttls", "none"],
    tls_verify: bool,
    ca_bundle: Optional[str],
    user: Optional[str],
    password: Optional[str],
    timeout: float,
) -> str:
    """Send an email via SMTP and return the Message-ID."""
    msg = EmailMessage(policy=SMTP_POLICY)  # RFC-compliant CRLF line endings
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    sender_domain = parseaddr(from_addr)[1].rpartition("@")[2]
    message_id = make_msgid(domain=sender_domain)
    msg["Message-ID"] = message_id
    msg.set_content("\n".join(body_lines))

    tls_context: Optional[ssl.SSLContext] = None
    if tls_mode in ("tls", "starttls"):
        tls_context = ssl.create_default_context(cafile=ca_bundle)
        if not tls_verify:
            tls_context.check_hostname = False  # must precede CERT_NONE
            tls_context.verify_mode = ssl.CERT_NONE

    if tls_mode == "tls":
        client = smtplib.SMTP_SSL(host, port, timeout=timeout, context=tls_context)
    else:
        client = smtplib.SMTP(host, port, timeout=timeout)

    with client:
        if tls_mode == "starttls":
            client.starttls(context=tls_context)
            client.ehlo()
        if user is not None and password is not None:
            client.login(user, password)
        refused = client.send_message(msg, to_addrs=list(to_addrs))
        if refused:
            raise smtplib.SMTPRecipientsRefused(refused)

    return message_id


class PhishMailer(Responder):
    def __init__(self):
        Responder.__init__(self)
        self.from_addr = self.get_param('config.from_addr', None, "Missing from address")
        self.smtp_host = self.get_param('config.smtp_host', None, "Missing SMTP host")
        self.smtp_encryption = self.get_param('config.smtp_encryption', None, "Missing encryption mode")
        self.smtp_verify = bool(self.get_param('config.smtp_verify', None, "Missing tls verify"))
        self.smtp_user = self.get_param('config.smtp_user', None, None)
        self.smtp_password = self.get_param('config.smtp_password', None, None)

        self.title = self.get_param('data.title', None)
        self.entity_id = self.get_param('data.caseId', None) or self.get_param('data.id', None)
        self.description_lines = self.get_param('data.description', None, "Can't get description").splitlines()

        self.ca_bundle = self.get_param('config.cafile', None)

        # config validation
        try:
            self.smtp_port = int(self.get_param('config.smtp_port', None, "Missing SMTP port"))
        except (TypeError, ValueError):
            self.error("smtp_port must be a number")
        if self.smtp_encryption not in TLS_MODES:
            self.error(f"Invalid smtp_encryption {self.smtp_encryption!r}; "
                       f"must be one of: {', '.join(TLS_MODES)}")
        if (self.smtp_user is None) != (self.smtp_password is None):
            self.error("smtp_user and smtp_password must be provided together")
        if self.smtp_user is not None and self.smtp_encryption == "none":
            self.error("Refusing to send credentials over an unencrypted "
                       "connection; use smtp_encryption 'tls' or 'starttls'")
        try:
            valid = validate_email(self.from_addr, check_deliverability=False)
            self.from_addr = getattr(valid, 'normalized', None)
        except EmailNotValidError as exc:
            self.error(f"Invalid from_addr: {exc}")

    def run(self):
        Responder.run(self)

        try:
            recipients, subject, start_index = extract_recipients(self.description_lines)
            if subject is None:
                subject = self.default_subject()
            body_lines = self.description_lines[start_index:]

            message_id = send_email(
                from_addr=self.from_addr,
                to_addrs=recipients,
                subject=subject,
                body_lines=body_lines,
                host=self.smtp_host,
                port=self.smtp_port,
                tls_mode=self.smtp_encryption,
                tls_verify=self.smtp_verify,
                user=self.smtp_user,
                password=self.smtp_password,
                ca_bundle=self.ca_bundle,
                timeout=30
            )

            self.report({
                'message': 'Mail sent',
                'recipients': recipients,
                'subject': subject,
                'message_id': message_id,
            })

        except NoRecipientFoundError:
            self.error('No recipient found in description.')
        except InvalidDirectiveError as exc:
            self.error(f'Invalid {MARKER} directive: {exc}')
        except EmailNotValidError:
            self.error("Recipient email found but invalid.")
        except (smtplib.SMTPException, ssl.SSLError, OSError) as exc:
            self.error(f'SMTP error: {exc}')
        except Exception as exc:
            self.error(str(exc))

    def default_subject(self) -> str:
        kind = "Task" if self.data_type == "thehive:case_task" else "Case"
        title = (self.title or "").replace("\r", " ").replace("\n", " ").strip()
        title = _truncate(title, SUBJECT_TITLE_LIMIT)
        subject = f"TheHive {kind} [{self.entity_id or 'unknown'}]: {title}"
        return _truncate(subject, MAX_SUBJECT_LEN)

    def operations(self, raw):
        return [self.build_operation('AddTagToCase', tag='PhishMailer:mail-sent')]


if __name__ == '__main__':
    PhishMailer().run()