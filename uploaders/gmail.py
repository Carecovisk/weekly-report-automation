"""
uploaders/gmail.py

Sends the weekly report email via SMTP with an app password.
Attaches both the HTML and Markdown files; the body is a plain-text summary.
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
    html_path: Path,
    markdown_path: Path,
    drive_link: str | None = None,
) -> None:
    """
    Send a multipart email:
      - Plain-text body with an optional Google Drive link
      - HTML report attached
      - Markdown report attached
    """
    msg = MIMEMultipart("mixed")
    msg["From"] = cfg.email_sender
    msg["To"] = cfg.email_recipient
    msg["Subject"] = subject

    # ── Plain-text body ────────────────────────────────────────────────────────
    body_lines = ["Relatorios semanais estão anexados. Baixe o relatório HTML e abra no navegador para a melhor experiência de visualização."]
    if drive_link:
        body_lines.append(f"\nVeja no Google Drive: {drive_link}")
    msg.attach(MIMEText("\n".join(body_lines), "plain"))

    # ── HTML attachment ────────────────────────────────────────────────────────
    html_bytes = html_path.read_bytes()
    html_attachment = MIMEApplication(html_bytes, Name=html_path.name)
    html_attachment["Content-Disposition"] = f'attachment; filename="{html_path.name}"'
    msg.attach(html_attachment)

    # ── Markdown attachment ────────────────────────────────────────────────────
    md_bytes = markdown_path.read_bytes()
    md_attachment = MIMEApplication(md_bytes, Name=markdown_path.name)
    md_attachment["Content-Disposition"] = f'attachment; filename="{markdown_path.name}"'
    msg.attach(md_attachment)

    # ── Send via SMTP ──────────────────────────────────────────────────────────
    with smtplib.SMTP(cfg.email_smtp_host, cfg.email_smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(cfg.email_sender, cfg.email_app_password)
        server.sendmail(cfg.email_sender, cfg.email_recipient, msg.as_bytes())

    log.info("Email sent to %s — subject: %s", cfg.email_recipient, subject)
