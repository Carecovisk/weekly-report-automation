"""
config.py — centralised settings loaded from the .env file.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Missing required environment variable: {key}")
    return val


def _csv(key: str, default: str = "") -> list[str]:
    raw = os.getenv(key, default)
    return [s.strip() for s in raw.split(",") if s.strip()]


@dataclass
class Config:
    # GitHub
    github_token: str = field(default_factory=lambda: _require("GITHUB_TOKEN"))
    github_org: str = field(default_factory=lambda: _require("GITHUB_ORG"))
    github_ignore_logins: set[str] = field(
        default_factory=lambda: set(_csv("GITHUB_IGNORE_LOGINS"))
    )

    # Trello
    trello_api_key: str = field(default_factory=lambda: _require("TRELLO_API_KEY"))
    trello_token: str = field(default_factory=lambda: _require("TRELLO_TOKEN"))
    trello_board_ids: list[str] = field(
        default_factory=lambda: _csv("TRELLO_BOARD_IDS")
    )
    trello_done_list_names: list[str] = field(
        default_factory=lambda: _csv("TRELLO_DONE_LIST_NAMES", "Done,Completed,Finished")
    )

    # Google
    google_drive_folder_id: str = field(
        default_factory=lambda: _require("GOOGLE_DRIVE_FOLDER_ID")
    )
    google_credentials_file: Path = field(
        default_factory=lambda: Path(os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json"))
    )
    google_token_file: Path = field(
        default_factory=lambda: Path(os.getenv("GOOGLE_TOKEN_FILE", "token.json"))
    )

    # Email
    email_sender: str = field(default_factory=lambda: _require("EMAIL_SENDER"))
    email_recipient: str = field(default_factory=lambda: _require("EMAIL_RECIPIENT"))
    email_subject_template: str = field(
        default_factory=lambda: os.getenv(
            "EMAIL_SUBJECT_TEMPLATE", "Weekly Team Report – {week_range}"
        )
    )

    # Optional developer name mapping  {"github_login": "Full Name"}
    developer_name_map: dict[str, str] = field(
        default_factory=lambda: json.loads(os.getenv("DEVELOPER_NAME_MAP", "{}"))
    )

    def display_name(self, login: str) -> str:
        return self.developer_name_map.get(login, login)
