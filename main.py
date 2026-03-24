"""
main.py — Weekly Team Report Generator

Usage:
  python main.py                    # current week
  python main.py --date 2025-03-10  # week containing this date
  python main.py --dry-run          # skip Drive upload & email
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config import Config
from fetchers.github_fetcher import fetch_github_activity
from fetchers.trello_fetcher import fetch_trello_activity
from reporters.builder import build_report
from reporters.ai_summarizer import generate_summaries
from reporters.html_renderer import render_html
from reporters.markdown_renderer import render_markdown
from uploaders.gmail import send_report_email
from uploaders.google_drive import upload_to_drive

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("main")


def _week_bounds(reference: datetime) -> tuple[datetime, datetime]:
    """Return Monday 00:00 UTC and Sunday 23:59:59 UTC for the week containing *reference*."""
    monday = reference - timedelta(days=reference.weekday())
    week_start = monday.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    week_end = (week_start + timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
    return week_start, week_end


def _output_dir(week_start: datetime) -> Path:
    path = Path("output") / f"week-{week_start:%Y-%m-%d}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate weekly team progress report")
    parser.add_argument("--date", help="ISO date within the target week (default: today)")
    parser.add_argument("--dry-run", action="store_true", help="Skip Drive upload and email")
    args = parser.parse_args()

    reference = (
        datetime.fromisoformat(args.date) if args.date else datetime.now(tz=timezone.utc)
    )
    week_start, week_end = _week_bounds(reference)

    log.info("Generating report for week %s → %s", week_start.date(), week_end.date())

    cfg = Config()
    out_dir = _output_dir(week_start)

    # ── 1. Fetch data ──────────────────────────────────────────────────────────
    log.info("Fetching GitHub activity…")
    github_activity = fetch_github_activity(cfg, since=week_start, until=week_end)

    if cfg.trello_enabled:
        log.info("Fetching Trello activity…")
        trello_activity = fetch_trello_activity(cfg, since=week_start, until=week_end)
    else:
        log.info("TRELLO_API_KEY/TRELLO_TOKEN not set — skipping Trello.")
        trello_activity = {}

    # ── 2. Build report model ──────────────────────────────────────────────────
    report = build_report(cfg, week_start, week_end, github_activity, trello_activity)
    log.info(
        "Report built: %d developers, %d commits, %d PRs, %d tasks",
        len(report.developers),
        report.total_commits,
        report.total_prs,
        report.total_tasks,
    )

    if not report.developers:
        log.warning("No activity found for this week — aborting.")
        sys.exit(0)

    # ── 2b. Generate AI summaries ──────────────────────────────────────────────
    if cfg.gemini_api_key:
        log.info("Generating AI summaries via Gemini…")
        generate_summaries(report, cfg.gemini_api_key)
    else:
        log.info("GEMINI_API_KEY not set — skipping AI summaries.")

    # ── 3. Render files ────────────────────────────────────────────────────────
    md_content = render_markdown(report)
    html_content = render_html(report)

    slug = f"team-report-{week_start:%Y-%m-%d}"
    md_path = out_dir / f"{slug}.md"
    html_path = out_dir / f"{slug}.html"

    md_path.write_text(md_content, encoding="utf-8")
    html_path.write_text(html_content, encoding="utf-8")
    log.info("Reports written to %s", out_dir)

    if args.dry_run:
        log.info("--dry-run: skipping Drive upload and email.")
        print(f"\n✅ Done (dry run). Files saved to: {out_dir}")
        return

    # ── 4. Upload to Google Drive ─────────────────────────────────────────────
    log.info("Uploading to Google Drive…")
    drive_link_md   = upload_to_drive(cfg, md_path,   "text/markdown")
    drive_link_html = upload_to_drive(cfg, html_path, "text/html")
    # Surface the HTML link as the primary share link
    drive_link = drive_link_html or drive_link_md

    # ── 5. Send email ─────────────────────────────────────────────────────────
    subject = cfg.email_subject_template.format(week_range=report.week_range)
    log.info("Sending email to %s…", cfg.email_recipient)
    send_report_email(
        cfg,
        subject=subject,
        html_body=html_content,
        markdown_path=md_path,
        drive_link=drive_link,
    )

    print(f"\n✅ Done! Report delivered.")
    print(f"   • Drive: {drive_link}")
    print(f"   • Email sent to: {cfg.email_recipient}")
    print(f"   • Local files: {out_dir}")


if __name__ == "__main__":
    main()
