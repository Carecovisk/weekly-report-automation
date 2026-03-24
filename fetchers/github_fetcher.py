"""
fetchers/github_fetcher.py

Fetches all commits and pull requests across the GitHub organisation
for a given date range, grouped by author login.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from github import Github, GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository

from config import Config

log = logging.getLogger(__name__)


@dataclass
class CommitInfo:
    sha: str
    message: str
    repo: str
    url: str
    authored_at: datetime


@dataclass
class PRInfo:
    number: int
    title: str
    repo: str
    url: str
    state: str          # "open" | "closed" | "merged"
    merged_at: datetime | None
    created_at: datetime


@dataclass
class DeveloperGitHubActivity:
    login: str
    commits: list[CommitInfo] = field(default_factory=list)
    pull_requests: list[PRInfo] = field(default_factory=list)


def fetch_github_activity(
    cfg: Config,
    since: datetime,
    until: datetime,
) -> dict[str, DeveloperGitHubActivity]:
    """
    Returns a dict keyed by GitHub login with all commits and PRs
    that fall within [since, until].
    """
    gh = Github(cfg.github_token, per_page=100)
    org = gh.get_organization(cfg.github_org)
    activity: dict[str, DeveloperGitHubActivity] = {}

    def get_or_create(login: str) -> DeveloperGitHubActivity:
        if login not in activity:
            activity[login] = DeveloperGitHubActivity(login=login)
        return activity[login]

    repos = list(org.get_repos(type="all"))
    log.info("Scanning %d repositories in org '%s'", len(repos), cfg.github_org)

    for repo in repos:
        _process_repo(repo, cfg, since, until, get_or_create)

    # Remove ignored logins
    for login in cfg.github_ignore_logins:
        activity.pop(login, None)

    log.info("GitHub activity fetched for %d developers", len(activity))
    return activity


def _process_repo(
    repo: Repository,
    cfg: Config,
    since: datetime,
    until: datetime,
    get_or_create,
) -> None:
    repo_name = repo.full_name

    # ── Commits ──────────────────────────────────────────────────────────────
    try:
        commits = repo.get_commits(since=since, until=until)
        for commit in commits:
            if commit.author is None:
                continue
            login = commit.author.login
            if login in cfg.github_ignore_logins:
                continue
            authored_at = commit.commit.author.date
            if not _in_range(authored_at, since, until):
                continue
            get_or_create(login).commits.append(
                CommitInfo(
                    sha=commit.sha[:7],
                    message=commit.commit.message.splitlines()[0],
                    repo=repo_name,
                    url=commit.html_url,
                    authored_at=authored_at,
                )
            )
    except GithubException as exc:
        log.warning("Could not fetch commits for %s: %s", repo_name, exc)

    # ── Pull Requests ─────────────────────────────────────────────────────────
    try:
        # Fetch both open and closed PRs; filter by date manually
        for state in ("open", "closed"):
            for pr in repo.get_pulls(state=state, sort="updated", direction="desc"):
                # Stop early once PRs are older than our window
                if pr.updated_at < since:
                    break
                if not _pr_in_range(pr, since, until):
                    continue
                login = pr.user.login if pr.user else None
                if not login or login in cfg.github_ignore_logins:
                    continue
                pr_state = "merged" if pr.merged_at else pr.state
                get_or_create(login).pull_requests.append(
                    PRInfo(
                        number=pr.number,
                        title=pr.title,
                        repo=repo_name,
                        url=pr.html_url,
                        state=pr_state,
                        merged_at=pr.merged_at,
                        created_at=pr.created_at,
                    )
                )
    except GithubException as exc:
        log.warning("Could not fetch PRs for %s: %s", repo_name, exc)


def _in_range(dt: datetime, since: datetime, until: datetime) -> bool:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return since <= dt <= until


def _pr_in_range(pr: PullRequest, since: datetime, until: datetime) -> bool:
    """A PR is 'in range' if it was created, merged, or updated during the window."""
    candidates = [pr.created_at, pr.merged_at, pr.updated_at]
    return any(d and _in_range(d, since, until) for d in candidates)
