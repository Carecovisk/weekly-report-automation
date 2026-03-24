"""
reporters/ai_summarizer.py

Generates concise per-developer AI summaries in Portuguese using the Gemini API.
"""
from __future__ import annotations

import logging

from google import genai

from reporters.builder import DeveloperReport, WeeklyReport

log = logging.getLogger(__name__)

_MODEL = "gemini-flash-latest"


def generate_summaries(report: WeeklyReport, api_key: str) -> None:
    """Populate ``dev.ai_summary`` for every developer in the report, in-place.

    Silently skips individual failures so the rest of the report is unaffected.
    """
    client = genai.Client(api_key=api_key)

    for dev in report.developers:
        try:
            dev.ai_summary = _summarize(client, dev, report)
        except Exception as exc:
            log.warning("Gemini summary failed for %s: %s", dev.display_name, exc)
            dev.ai_summary = ""


def _summarize(client: genai.Client, dev: DeveloperReport, report: WeeklyReport) -> str:
    parts: list[str] = []

    if dev.commits:
        msgs = "; ".join(c.message for c in dev.commits[:12])
        parts.append(f"Commits ({dev.commit_count}): {msgs}")

    if dev.pull_requests:
        prs = "; ".join(
            f"#{pr.number} {pr.title} [{pr.state}]" for pr in dev.pull_requests[:12]
        )
        parts.append(f"Pull Requests ({dev.pr_count}): {prs}")

    if dev.trello_cards:
        tasks = "; ".join(c.name for c in dev.trello_cards[:12])
        parts.append(f"Tarefas concluídas ({dev.task_count}): {tasks}")

    activity = "\n".join(parts) if parts else "Nenhuma atividade registrada."

    prompt = (
        "Você é um assistente que resume atividades semanais de desenvolvedores de software.\n"
        f"Escreva um resumo conciso em português do Brasil, com no máximo 4 linhas, sobre o que "
        f"o desenvolvedor '{dev.display_name}' realizou na semana de "
        f"{report.week_start:%d/%m/%Y} a {report.week_end:%d/%m/%Y}.\n"
        "Seja direto, objetivo e profissional. Não use marcadores ou listas.\n\n"
        f"{activity}"
    )

    response = client.models.generate_content(model=_MODEL, contents=prompt)
    return response.text.strip()
