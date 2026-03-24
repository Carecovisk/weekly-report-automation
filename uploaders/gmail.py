"""
uploaders/gmail.py

Sends the weekly report email via SMTP with an app password.
Attaches the Markdown file and embeds the HTML as the email body.
"""
from __future__ import annotations

import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from config import Config

log = logging.getLogger(__name__)


def send_report_email(
    cfg: Config,
    subject: str,
    html_body: str,
    markdown_path: Path,
    drive_link: str | None = None,
) -> None:
    """
    Send a multipart email:
      - HTML body (the report)
      - Markdown file attached
      - Optional Google Drive link appended to body
    """
    msg = MIMEMultipart("mixed")
    msg["From"] = cfg.email_sender
    msg["To"] = cfg.email_recipient
    msg["Subject"] = subject

    # ── HTML body ──────────────────────────────────────────────────────────────
    body_html = html_body
    if drive_link:
        drive_note = (
            f'<p style="font-family:sans-serif;color:#8892a4;font-size:13px;margin-top:2rem">'
            f'📁 <a href="{drive_link}">View full report on Google Drive</a></p>'
        )
        body_html = body_html.replace("</body>", drive_note + "\n</body>")

    msg.attach(MIMEText(body_html, "html"))

    # ── Markdown attachment ────────────────────────────────────────────────────
    md_bytes = markdown_path.read_bytes()
    attachment = MIMEApplication(md_bytes, Name=markdown_path.name)
    attachment["Content-Disposition"] = f'attachment; filename="{markdown_path.name}"'
    msg.attach(attachment)

    # ── Send via SMTP ──────────────────────────────────────────────────────────
    with smtplib.SMTP(cfg.email_smtp_host, cfg.email_smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(cfg.email_sender, cfg.email_app_password)
        server.sendmail(cfg.email_sender, cfg.email_recipient, msg.as_bytes())

    log.info("Email sent to %s — subject: %s", cfg.email_recipient, subject)
