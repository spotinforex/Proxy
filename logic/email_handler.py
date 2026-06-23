import email.utils
import json
import logging
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import httpx
from dotenv import load_dotenv

from utils.retry import retry

load_dotenv()

log = logging.getLogger(__name__)

SMTP_HOST    = os.getenv("smtp-host")
SMTP_PORT    = int(os.getenv("smtp-port", 587))
SMTP_USER    = os.getenv("smtp-user")
SMTP_PASS    = os.getenv("smtp-pass")
SENDER       = os.getenv("smtp-user")
CC_RECIPIENT = os.getenv("CC_RECIPIENT", "")

SENDER_NAME  = os.getenv("SENDER_NAME", "MCIPP Support")


# ── SMTP ──────────────────────────────────────────────────────────────────────

def connect_smtp() -> smtplib.SMTP:
    log.info(f"Connecting to SMTP {SMTP_HOST}:{SMTP_PORT}...")
    if SMTP_PORT == 465:
        smtp = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30)
        smtp.ehlo()
    elif SMTP_PORT in (587, 2525):
        smtp = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
    else:
        smtp = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
        smtp.ehlo()
    smtp.login(SMTP_USER, SMTP_PASS)
    log.info("SMTP authenticated.")
    return smtp


@retry(max_attempts=3, delay=2.0, backoff=2.0)
def smtp_send(smtp: smtplib.SMTP, msg: MIMEMultipart, recipients: list[str]):
    smtp.sendmail(SENDER, recipients, msg.as_string())


# ── Attachment Fetcher ────────────────────────────────────────────────────────

def _fetch_attachment(source: str) -> tuple[bytes, str] | None:
    """
    Accepts a URL or a local file path.
    Returns (bytes, filename) or None if unavailable.
    """
    # Normalise backslashes from Windows paths stored in DB
    source = source.replace("\\", "/")

    if source.startswith("http://") or source.startswith("https://"):
        try:
            response = httpx.get(source, timeout=30, follow_redirects=True)
            response.raise_for_status()
            # Derive filename from URL, fall back to attachment.pdf
            filename = source.rstrip("/").split("/")[-1] or "attachment.pdf"
            if "." not in filename:
                filename += ".pdf"
            log.info(f"Downloaded attachment: {filename} from {source}")
            return response.content, filename
        except Exception as e:
            log.error(f"Failed to download attachment from {source}: {e}")
            return None
    else:
        path = Path(source)
        if path.exists():
            return path.read_bytes(), path.name
        log.warning(f"Attachment not found, skipping: {path}")
        return None


# ── Email Builder ─────────────────────────────────────────────────────────────

def build_email(
    recipient: str,
    subject: str,
    body: str,
    attachment_paths: list[str] = None,
) -> MIMEMultipart:
    sender_domain = SENDER.split("@")[1] if SENDER and "@" in SENDER else "mcipp.org"

    msg = MIMEMultipart()
    msg["From"]       = f"{SENDER_NAME} <{SENDER}>"
    msg["To"]         = recipient
    msg["Subject"]    = subject
    msg["Date"]       = email.utils.formatdate(localtime=True)
    msg["Message-ID"] = email.utils.make_msgid(domain=sender_domain)

    if CC_RECIPIENT:
        msg["Cc"] = CC_RECIPIENT

    msg.attach(MIMEText(body, "plain"))

    for source in (attachment_paths or []):
        result = _fetch_attachment(source)
        if result:
            data, filename = result
            part = MIMEBase("application", "octet-stream")
            part.set_payload(data)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
            msg.attach(part)

    return msg


# ── Tool Definitions ──────────────────────────────────────────────────────────

EMAIL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "send_certificate_email",
            "description": (
                "Sends an email to a business owner with their CAC registration "
                "certificate and status report attached. Draft the subject and body "
                "before calling this tool."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient_email": {
                        "type": "string",
                        "description": "The business owner's email address"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line"
                    },
                    "body": {
                        "type": "string",
                        "description": "Full email body — warm, professional, plain English"
                    },
                    "owner_name": {
                        "type": "string",
                        "description": "Full name of the business owner"
                    },
                    "business_name": {
                        "type": "string",
                        "description": "Registered business name"
                    },
                    "certificate_path": {
                        "type": "string",
                        "description": "URL or local path to the certificate PDF. Null if not available."
                    },
                    "status_report_path": {
                        "type": "string",
                        "description": "URL or local path to the status report PDF. Null if not available."
                    }
                },
                "required": ["recipient_email", "subject", "body", "owner_name", "business_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_status_email",
            "description": (
                "Sends a plain-English status update email to a business owner — "
                "no attachments. Used when registration is pending or more information "
                "is needed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient_email": {"type": "string"},
                    "subject":         {"type": "string"},
                    "body":            {"type": "string"},
                    "owner_name":      {"type": "string"},
                    "business_name":   {"type": "string"}
                },
                "required": ["recipient_email", "subject", "body", "owner_name", "business_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "notify_staff",
            "description": "Sends an escalation email to a staff member with full complaint context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "staff_email": {"type": "string"},
                    "subject":     {"type": "string"},
                    "body":        {"type": "string"}
                },
                "required": ["staff_email", "subject", "body"]
            }
        }
    }
]


# ── Tool Executor ─────────────────────────────────────────────────────────────

def execute_email_tool(tool_name: str, tool_args: dict) -> str:
    try:
        smtp = connect_smtp()

        if tool_name == "send_certificate_email":
            attachments = []
            if tool_args.get("certificate_path"):
                attachments.append(tool_args["certificate_path"])
            if tool_args.get("status_report_path"):
                attachments.append(tool_args["status_report_path"])

            recipients = [tool_args["recipient_email"]]
            if CC_RECIPIENT:
                recipients.append(CC_RECIPIENT)

            msg = build_email(
                recipient=tool_args["recipient_email"],
                subject=tool_args["subject"],
                body=tool_args["body"],
                attachment_paths=attachments,
            )
            smtp_send(smtp, msg, recipients)
            smtp.quit()
            log.info(f"Certificate email sent to {tool_args['recipient_email']}")
            return json.dumps({"status": "sent", "to": tool_args["recipient_email"]})

        if tool_name == "send_status_email":
            recipients = [tool_args["recipient_email"]]
            if CC_RECIPIENT:
                recipients.append(CC_RECIPIENT)

            msg = build_email(
                recipient=tool_args["recipient_email"],
                subject=tool_args["subject"],
                body=tool_args["body"],
            )
            smtp_send(smtp, msg, recipients)
            smtp.quit()
            log.info(f"Status email sent to {tool_args['recipient_email']}")
            return json.dumps({"status": "sent", "to": tool_args["recipient_email"]})

        if tool_name == "notify_staff":
            msg = build_email(
                recipient=tool_args["staff_email"],
                subject=tool_args["subject"],
                body=tool_args["body"],
            )
            smtp_send(smtp, msg, [tool_args["staff_email"]])
            smtp.quit()
            log.info(f"Staff email sent to {tool_args['staff_email']}")
            return json.dumps({"status": "notified", "to": tool_args["staff_email"]})

        smtp.quit()
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    except Exception as e:
        log.error(f"Email tool execution failed — {tool_name}: {e}")
        return json.dumps({"error": str(e)})