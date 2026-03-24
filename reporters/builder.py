"""
reporters/builder.py

Merges GitHub and Trello activity into a unified per-developer report model.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from config import Config
from fetchers.github_fetcher import CommitInfo, DeveloperGitHubActivity, PRInfo
from fetchers.trello_fetcher import DeveloperTrelloActivity, TrelloCard


@dataclass
class DeveloperReport:
    login: str                          # GitHub login (primary key)
    display_name: str
    commits: list[CommitInfo] = field(default_factory=list)
    pull_requests: list[PRInfo] = field(default_factory=list)
    trello_cards: list[TrelloCard] = field(default_factory=list)
    ai_summary: str = ""                # Populated by ai_summarizer if Gemini is configured

    @property
    def has_activity(self) -> bool:
        return bool(self.commits or self.pull_requests or self.trello_cards)

    @property
    def commit_count(self) -> int:
        return len(self.commits)

    @property
    def pr_count(self) -> int:
        return len(self.pull_requests)

    @property
    def merged_pr_count(self) -> int:
        return sum(1 for pr in self.pull_requests if pr.state == "merged")

    @property
    def task_count(self) -> int:
        return len(self.trello_cards)

    @property
    def repos_touched(self) -> list[str]:
        seen: set[str] = set()
        result = []
        for c in self.commits:
            if c.repo not in seen:
                seen.add(c.repo)
                result.append(c.repo)
        for pr in self.pull_requests:
            if pr.repo not in seen:
                seen.add(pr.repo)
                result.append(pr.repo)
        return result


@dataclass
class WeeklyReport:
    week_start: datetime
    week_end: datetime
    org: str
    developers: list[DeveloperReport]

    @property
    def week_range(self) -> str:
        return f"{self.week_start:%b %d} – {self.week_end:%b %d, %Y}"

    @property
    def total_commits(self) -> int:
        return sum(d.commit_count for d in self.developers)

    @property
    def total_prs(self) -> int:
        return sum(d.pr_count for d in self.developers)

    @property
    def total_tasks(self) -> int:
        return sum(d.task_count for d in self.developers)


def build_report(
    cfg: Config,
    week_start: datetime,
    week_end: datetime,
    github_activity: dict[str, DeveloperGitHubActivity],
    trello_activity: dict[str, DeveloperTrelloActivity],
) -> WeeklyReport:
    """
    Merge GitHub and Trello data into a WeeklyReport.

    Trello members are matched to GitHub logins via the developer_name_map or
    by username similarity as a best-effort fallback.
    """
    dev_reports: dict[str, DeveloperReport] = {}

    # Index Trello activity for fuzzy matching
    # Map: trello_username → DeveloperTrelloActivity
    trello_by_username = trello_activity  # already keyed by username

    # Build the reverse lookup: display_name → github_login (from name map)
    name_to_login = {v.lower(): k for k, v in cfg.developer_name_map.items()}

    def get_or_create(login: str) -> DeveloperReport:
        if login not in dev_reports:
            dev_reports[login] = DeveloperReport(
                login=login,
                display_name=cfg.display_name(login),
            )
        return dev_reports[login]

    # Populate from GitHub
    for login, gh_dev in github_activity.items():
        dev = get_or_create(login)
        dev.commits.extend(gh_dev.commits)
        dev.pull_requests.extend(gh_dev.pull_requests)

    # Populate from Trello — match by configured name map or username
    for trello_username, trello_dev in trello_by_username.items():
        # 1. Try explicit mapping via full name
        github_login = name_to_login.get(trello_dev.full_name.lower())
        # 2. Try matching trello username == github login
        if not github_login and trello_username in dev_reports:
            github_login = trello_username
        # 3. Create a standalone entry keyed by trello username
        if not github_login:
            github_login = trello_username

        dev = get_or_create(github_login)
        if dev.display_name == github_login:
            # Prefer the Trello full name if we don't have a mapping
            dev.display_name = trello_dev.full_name
        dev.trello_cards.extend(trello_dev.cards)

    # Sort developers by activity (most active first), then alphabetically
    sorted_devs = sorted(
        (d for d in dev_reports.values() if d.has_activity),
        key=lambda d: (-(d.commit_count + d.pr_count + d.task_count), d.display_name.lower()),
    )

    return WeeklyReport(
        week_start=week_start,
        week_end=week_end,
        org=cfg.github_org,
        developers=sorted_devs,
    )
