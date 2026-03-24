"""
uploaders/google_drive.py

Uploads files to a specific Google Drive folder using the Drive v3 API.
Handles OAuth2 token refresh automatically.
"""
from __future__ import annotations

import logging
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config import Config

log = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/gmail.send",
]


def _get_credentials(cfg: Config) -> Credentials:
    creds: Credentials | None = None

    if cfg.google_token_file.exists():
        creds = Credentials.from_authorized_user_file(str(cfg.google_token_file), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(cfg.google_credentials_file), SCOPES
            )
            creds = flow.run_local_server(port=0)
        cfg.google_token_file.write_text(creds.to_json())

    return creds


def upload_to_drive(cfg: Config, file_path: Path, mime_type: str) -> str:
    """
    Upload *file_path* to the configured Drive folder.
    Returns the shareable web view link of the uploaded file.
    """
    creds = _get_credentials(cfg)
    service = build("drive", "v3", credentials=creds)

    file_metadata = {
        "name": file_path.name,
        "parents": [cfg.google_drive_folder_id],
    }
    media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)

    uploaded = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id,webViewLink")
        .execute()
    )

    link = uploaded.get("webViewLink", "")
    log.info("Uploaded '%s' to Drive → %s", file_path.name, link)
    return link
