# Weekly Team Report Automation

Fetches GitHub commits/PRs + Trello tasks, generates Markdown/HTML reports per developer, uploads to Google Drive, and emails your boss.

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure credentials
Copy `.env.example` to `.env` and fill in all values.

```bash
cp .env.example .env
```

### 3. Google credentials
- Go to [Google Cloud Console](https://console.cloud.google.com)
- Enable **Gmail API** and **Google Drive API**
- Create OAuth2 credentials → download as `credentials.json` in the project root
- On first run, a browser will open to authorize. A `token.json` will be saved for future runs.

### 4. Run
```bash
# Generate report for the current week
python main.py

# Generate report for a specific week (any date within the week)
python main.py --date 2025-03-10

# Dry run (generate reports locally, skip Drive upload and email)
python main.py --dry-run
```

## Project Structure
```
weekly-report-automation/
├── main.py                  # Entry point & orchestration
├── config.py                # Settings loaded from .env
├── fetchers/
│   ├── github_fetcher.py    # GitHub commits & PRs
│   └── trello_fetcher.py    # Trello completed cards
├── reporters/
│   ├── builder.py           # Aggregates data per developer
│   ├── markdown_renderer.py # Renders Markdown report
│   └── html_renderer.py     # Renders HTML report
├── uploaders/
│   ├── google_drive.py      # Uploads files to Drive
│   └── gmail.py             # Sends email via Gmail API
├── requirements.txt
└── .env.example
```
