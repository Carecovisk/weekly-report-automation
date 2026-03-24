"""
reporters/markdown_renderer.py

Renders a WeeklyReport to a Markdown string.
"""
from __future__ import annotations

from reporters.builder import DeveloperReport, WeeklyReport


def render_markdown(report: WeeklyReport) -> str:
    lines: list[str] = []

    lines += [
        f"# Weekly Team Report — {report.week_range}",
        "",
        f"**Organisation:** {report.org}  ",
        f"**Period:** {report.week_start:%Y-%m-%d} → {report.week_end:%Y-%m-%d}  ",
        f"**Developers active:** {len(report.developers)}  ",
        f"**Total commits:** {report.total_commits}  ",
        f"**Total PRs:** {report.total_prs}  ",
        f"**Total tasks completed:** {report.total_tasks}",
        "",
        "---",
        "",
        "## Summary",
        "",
        _summary_table(report),
        "",
        "---",
        "",
        "## Developer Breakdown",
        "",
    ]

    for dev in report.developers:
        lines += _dev_section(dev)
        lines.append("")

    return "\n".join(lines)


def _summary_table(report: WeeklyReport) -> str:
    header = "| Developer | Commits | PRs (merged) | Tasks done |"
    sep    = "|-----------|:-------:|:------------:|:----------:|"
    rows = [
        f"| {d.display_name} | {d.commit_count} | {d.pr_count} ({d.merged_pr_count}) | {d.task_count} |"
        for d in report.developers
    ]
    return "\n".join([header, sep, *rows])


def _dev_section(dev: DeveloperReport) -> list[str]:
    lines: list[str] = [
        f"### {dev.display_name}",
        f"*GitHub:* `{dev.login}`  ",
        f"*Repos touched:* {', '.join(f'`{r}`' for r in dev.repos_touched) or '—'}",
        "",
    ]

    # Commits
    if dev.commits:
        lines.append("#### Commits")
        for c in sorted(dev.commits, key=lambda x: x.authored_at, reverse=True):
            lines.append(
                f"- [`{c.sha}`]({c.url}) **{c.repo}** — {_escape_md(c.message)}"
            )
        lines.append("")

    # Pull Requests
    if dev.pull_requests:
        lines.append("#### Pull Requests")
        for pr in sorted(dev.pull_requests, key=lambda x: x.created_at, reverse=True):
            badge = _pr_badge(pr.state)
            lines.append(
                f"- {badge} [#{pr.number}]({pr.url}) {_escape_md(pr.title)} *(in `{pr.repo}`)*"
            )
        lines.append("")

    # Trello tasks
    if dev.trello_cards:
        lines.append("#### Completed Tasks (Trello)")
        for card in sorted(dev.trello_cards, key=lambda x: x.last_activity, reverse=True):
            lines.append(
                f"- ✅ [{_escape_md(card.name)}]({card.url}) — *{card.board_name} / {card.list_name}*"
            )
        lines.append("")

    return lines


def _pr_badge(state: str) -> str:
    return {"merged": "🟣 Merged", "closed": "🔴 Closed", "open": "🟢 Open"}.get(state, state)


def _escape_md(text: str) -> str:
    # Escape a minimal set of Markdown special chars in user content
    for ch in ("*", "_", "`", "[", "]"):
        text = text.replace(ch, f"\\{ch}")
    return text
