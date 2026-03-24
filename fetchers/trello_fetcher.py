"""
fetchers/trello_fetcher.py

Fetches Trello cards that were moved into a "done" list during the week,
grouped by the last member who acted on them.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

import requests

from config import Config

log = logging.getLogger(__name__)

TRELLO_BASE = "https://api.trello.com/1"


@dataclass
class TrelloCard:
    card_id: str
    name: str
    board_name: str
    list_name: str
    url: str
    last_activity: datetime
    member_ids: list[str]   # Trello member IDs assigned


@dataclass
class DeveloperTrelloActivity:
    member_id: str
    username: str
    full_name: str
    cards: list[TrelloCard] = field(default_factory=list)


def fetch_trello_activity(
    cfg: Config,
    since: datetime,
    until: datetime,
) -> dict[str, DeveloperTrelloActivity]:
    """
    Returns a dict keyed by Trello username with cards completed in [since, until].
    """
    auth = {"key": cfg.trello_api_key, "token": cfg.trello_token}

    board_ids = cfg.trello_board_ids or _get_all_board_ids(auth)
    log.info("Scanning %d Trello board(s)", len(board_ids))

    # Resolve member IDs → profile once
    member_cache: dict[str, DeveloperTrelloActivity] = {}

    for board_id in board_ids:
        _process_board(board_id, cfg, auth, since, until, member_cache)

    log.info("Trello activity fetched for %d members", len(member_cache))
    return member_cache


def _get_all_board_ids(auth: dict) -> list[str]:
    resp = requests.get(f"{TRELLO_BASE}/members/me/boards", params={**auth, "fields": "id,name"})
    resp.raise_for_status()
    return [b["id"] for b in resp.json()]


def _process_board(
    board_id: str,
    cfg: Config,
    auth: dict,
    since: datetime,
    until: datetime,
    member_cache: dict[str, DeveloperTrelloActivity],
) -> None:
    # Get board name
    board_resp = requests.get(f"{TRELLO_BASE}/boards/{board_id}", params={**auth, "fields": "name"})
    board_resp.raise_for_status()
    board_name = board_resp.json()["name"]

    # Get lists
    lists_resp = requests.get(f"{TRELLO_BASE}/boards/{board_id}/lists", params={**auth, "fields": "id,name"})
    lists_resp.raise_for_status()
    done_list_ids = {
        lst["id"]: lst["name"]
        for lst in lists_resp.json()
        if _is_done_list(lst["name"], cfg.trello_done_list_names)
    }

    if not done_list_ids:
        log.debug("No 'done' lists found on board '%s'", board_name)
        return

    # Get cards in done lists
    cards_resp = requests.get(
        f"{TRELLO_BASE}/boards/{board_id}/cards",
        params={
            **auth,
            "fields": "id,name,idList,idMembers,dateLastActivity,shortUrl",
            "filter": "all",
        },
    )
    cards_resp.raise_for_status()

    for raw in cards_resp.json():
        if raw["idList"] not in done_list_ids:
            continue
        last_activity = _parse_dt(raw["dateLastActivity"])
        if not last_activity or not _in_range(last_activity, since, until):
            continue

        card = TrelloCard(
            card_id=raw["id"],
            name=raw["name"],
            board_name=board_name,
            list_name=done_list_ids[raw["idList"]],
            url=raw["shortUrl"],
            last_activity=last_activity,
            member_ids=raw.get("idMembers", []),
        )

        for member_id in card.member_ids:
            dev = _resolve_member(member_id, auth, member_cache)
            if dev:
                dev.cards.append(card)


def _resolve_member(
    member_id: str,
    auth: dict,
    cache: dict[str, DeveloperTrelloActivity],
) -> DeveloperTrelloActivity | None:
    # Already cached by member_id? Look it up by scanning values
    for dev in cache.values():
        if dev.member_id == member_id:
            return dev
    try:
        resp = requests.get(
            f"{TRELLO_BASE}/members/{member_id}",
            params={**auth, "fields": "id,username,fullName"},
        )
        resp.raise_for_status()
        data = resp.json()
        username = data["username"]
        dev = DeveloperTrelloActivity(
            member_id=data["id"],
            username=username,
            full_name=data.get("fullName", username),
        )
        cache[username] = dev
        return dev
    except Exception as exc:
        log.warning("Could not resolve Trello member %s: %s", member_id, exc)
        return None


def _is_done_list(list_name: str, done_names: list[str]) -> bool:
    lower = list_name.lower()
    return any(d.lower() in lower for d in done_names)


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def _in_range(dt: datetime, since: datetime, until: datetime) -> bool:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return since <= dt <= until
