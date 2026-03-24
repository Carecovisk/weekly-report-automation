"""
reporters/markdown_renderer.py

Renders a WeeklyReport to a Markdown string (in Portuguese).
"""
from __future__ import annotations

from reporters.builder import DeveloperReport, WeeklyReport


def render_markdown(report: WeeklyReport) -> str:
    lines: list[str] = []

    lines += [
        f"# Relatório Semanal da Equipe — {report.week_range}",
        "",
        f"**Organização:** {report.org}  ",
        f"**Período:** {report.week_start:%Y-%m-%d} → {report.week_end:%Y-%m-%d}  ",
        f"**Desenvolvedores ativos:** {len(report.developers)}  ",
        f"**Total de commits:** {report.total_commits}  ",
        f"**Total de PRs:** {report.total_prs}  ",
        f"**Total de tarefas concluídas:** {report.total_tasks}",
        "",
        "---",
        "",
        "## Resumo",
        "",
        _summary_table(report),
        "",
        "---",
        "",
        "## Detalhamento por Desenvolvedor",
        "",
    ]

    for dev in report.developers:
        lines += _dev_section(dev)
        lines.append("")

    return "\n".join(lines)


def _summary_table(report: WeeklyReport) -> str:
    header = "| Desenvolvedor | Commits | PRs (mesclados) | Tarefas |"
    sep    = "|---------------|:-------:|:---------------:|:-------:|"
    rows = [
        f"| {d.display_name} | {d.commit_count} | {d.pr_count} ({d.merged_pr_count}) | {d.task_count} |"
        for d in report.developers
    ]
    return "\n".join([header, sep, *rows])


def _dev_section(dev: DeveloperReport) -> list[str]:
    lines: list[str] = [
        f"### {dev.display_name}",
        f"*GitHub:* `{dev.login}`  ",
        f"*Repositórios:* {', '.join(f'`{r}`' for r in dev.repos_touched) or '—'}",
        "",
    ]

    if dev.ai_summary:
        lines += [
            "#### Resumo IA",
            dev.ai_summary,
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
                f"- {badge} [#{pr.number}]({pr.url}) {_escape_md(pr.title)} *(em `{pr.repo}`)*"
            )
        lines.append("")

    # Trello tasks
    if dev.trello_cards:
        lines.append("#### Tarefas Concluídas (Trello)")
        for card in sorted(dev.trello_cards, key=lambda x: x.last_activity, reverse=True):
            lines.append(
                f"- ✅ [{_escape_md(card.name)}]({card.url}) — *{card.board_name} / {card.list_name}*"
            )
        lines.append("")

    return lines


def _pr_badge(state: str) -> str:
    return {"merged": "🟣 Mesclado", "closed": "🔴 Fechado", "open": "🟢 Aberto"}.get(state, state)


def _escape_md(text: str) -> str:
    for ch in ("*", "_", "`", "[", "]"):
        text = text.replace(ch, f"\\{ch}")
    return text
