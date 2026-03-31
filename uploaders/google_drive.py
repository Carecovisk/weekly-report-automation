"""
uploaders/google_drive.py

Uploads files to a specific Google Drive folder using the Drive v3 API.
Uses a service account credentials file for authentication.
"""
from __future__ import annotations

import logging
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config import Config

log = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive"]


def _get_credentials(cfg: Config) -> service_account.Credentials:
    return service_account.Credentials.from_service_account_file(
        str(cfg.google_credentials_file), scopes=SCOPES
    )


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
        .create(
            body=file_metadata,
            media_body=media,
            fields="id,webViewLink",
            supportsAllDrives=True,
        )
        .execute()
    )

    link = uploaded.get("webViewLink", "")
    log.info("Uploaded '%s' to Drive → %s", file_path.name, link)
    return link
