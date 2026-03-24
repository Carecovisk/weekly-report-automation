# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

A Python CLI tool that generates weekly team progress reports by aggregating data from GitHub (commits/PRs) and Trello (completed cards), rendering them as Markdown and HTML, uploading to Google Drive, and emailing them to stakeholders.

## Running the tool

```bash
# Install dependencies
pip install -r requirements.txt

# Run for the current week
python main.py

# Run for a specific week (any date within that week)
python main.py --date 2025-03-10

# Dry run: generate local files only, skip uploads and email
python main.py --dry-run
```

Output files are written to `output/week-YYYY-MM-DD/` before any upload.

## Configuration

Copy `.env.example` to `.env` and fill in all credentials. Key variables:

- `GITHUB_TOKEN`, `GITHUB_ORG` — GitHub personal access token and org name
- `TRELLO_API_KEY`, `TRELLO_TOKEN` — Trello credentials
- `GOOGLE_DRIVE_FOLDER_ID`, `GOOGLE_CREDENTIALS_FILE` — Drive upload target; `credentials.json` is the OAuth2 client secret file downloaded from Google Cloud Console
- `EMAIL_SENDER`, `EMAIL_RECIPIENT` — Gmail sender/recipient
- `DEVELOPER_NAME_MAP` — JSON mapping GitHub logins to display names, used to merge identities across GitHub and Trello
- `GEMINI_API_KEY` — optional; when set, generates a concise Portuguese AI summary (≤4 lines) per developer via `gemini-2.0-flash`

Google OAuth tokens are cached in `token.json` after first authentication. Delete it to force re-authentication.

## Architecture

The pipeline runs in this order inside `main.py`:

1. **Fetch** — `fetchers/github_fetcher.py` collects commits and PRs from all repos in the org; `fetchers/trello_fetcher.py` collects cards from "Done" lists across configured boards. Each returns a dict keyed by username.

2. **Build** — `reporters/builder.py` merges GitHub and Trello activity per developer. The `DeveloperReport` dataclass includes an `ai_summary` field (empty string by default) that is populated in the next step.

2b. **AI Summaries** — `reporters/ai_summarizer.py` iterates over each developer and calls Gemini to generate a Portuguese summary from their commits, PRs, and Trello cards. Skipped silently if `GEMINI_API_KEY` is absent or a call fails. It attempts identity matching via `DEVELOPER_NAME_MAP`, then by username similarity. Produces `WeeklyReport` containing a list of `DeveloperReport` objects sorted by activity.

3. **Render** — `reporters/markdown_renderer.py` and `reporters/html_renderer.py` produce the two output formats. The HTML renderer uses Jinja2 with an embedded template (dark theme, CSS Grid).

4. **Upload** — `uploaders/google_drive.py` uploads both files to Drive via OAuth2; `uploaders/gmail.py` sends a multipart email (HTML body + Markdown attachment) with the Drive link appended.

The `--dry-run` flag skips steps 3 onward after saving local files.

## No tests or CI

There is no test suite or linting setup. The project is stateless (no database); all processing is in-memory per run.