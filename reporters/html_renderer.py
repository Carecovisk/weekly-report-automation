"""
reporters/html_renderer.py

Renders a WeeklyReport to a self-contained HTML string using Jinja2.
"""
from __future__ import annotations

from jinja2 import Environment, BaseLoader

from reporters.builder import WeeklyReport

_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Weekly Team Report — {{ report.week_range }}</title>
<style>
  :root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --border: #2a2d3a;
    --accent: #6c8ef5;
    --accent2: #a78bfa;
    --green: #34d399;
    --red: #f87171;
    --yellow: #fbbf24;
    --text: #e2e8f0;
    --muted: #8892a4;
    --font: 'Segoe UI', system-ui, sans-serif;
    --mono: 'Cascadia Code', 'Fira Code', monospace;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
    font-size: 15px;
    line-height: 1.7;
    padding: 2rem 1rem;
  }
  .container { max-width: 900px; margin: 0 auto; }

  /* Header */
  .report-header {
    background: linear-gradient(135deg, #1e2235 0%, #252a40 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2.5rem 2.5rem 2rem;
    margin-bottom: 2rem;
  }
  .report-header h1 {
    font-size: 1.9rem;
    font-weight: 700;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 1rem;
  }
  .meta-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 1rem;
    margin-top: 1.2rem;
  }
  .meta-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: .9rem 1rem;
    text-align: center;
  }
  .meta-card .num {
    font-size: 2rem;
    font-weight: 700;
    color: var(--accent);
    display: block;
  }
  .meta-card .label { color: var(--muted); font-size: .8rem; text-transform: uppercase; letter-spacing: .05em; }

  /* Summary table */
  .section { margin-bottom: 2.5rem; }
  .section h2 {
    font-size: 1.1rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: var(--muted);
    border-bottom: 1px solid var(--border);
    padding-bottom: .5rem;
    margin-bottom: 1.2rem;
  }
  table { width: 100%; border-collapse: collapse; }
  th {
    text-align: left;
    font-size: .75rem;
    text-transform: uppercase;
    letter-spacing: .06em;
    color: var(--muted);
    padding: .5rem .75rem;
    border-bottom: 1px solid var(--border);
  }
  td { padding: .6rem .75rem; border-bottom: 1px solid rgba(255,255,255,0.04); }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(255,255,255,0.025); }
  td.num { text-align: center; }
  .badge {
    display: inline-block;
    padding: .15rem .55rem;
    border-radius: 999px;
    font-size: .75rem;
    font-weight: 600;
  }
  .badge-merged { background: rgba(167,139,250,.15); color: var(--accent2); }
  .badge-open   { background: rgba(52,211,153,.15);  color: var(--green); }
  .badge-closed { background: rgba(248,113,113,.15); color: var(--red); }

  /* Developer cards */
  .dev-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    margin-bottom: 1.5rem;
    overflow: hidden;
  }
  .dev-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.1rem 1.5rem;
    border-bottom: 1px solid var(--border);
    background: rgba(108,142,245,.06);
  }
  .dev-name { font-size: 1.1rem; font-weight: 700; }
  .dev-login { font-family: var(--mono); font-size: .8rem; color: var(--muted); margin-top: .1rem; }
  .dev-stats { display: flex; gap: .75rem; }
  .stat-pill {
    font-size: .8rem;
    padding: .2rem .65rem;
    border-radius: 999px;
    border: 1px solid var(--border);
    color: var(--muted);
  }
  .stat-pill span { color: var(--text); font-weight: 600; }
  .dev-body { padding: 1.2rem 1.5rem; }
  .sub-section { margin-bottom: 1.2rem; }
  .sub-section:last-child { margin-bottom: 0; }
  .sub-title {
    font-size: .75rem;
    text-transform: uppercase;
    letter-spacing: .07em;
    color: var(--muted);
    margin-bottom: .6rem;
    font-weight: 600;
  }
  .item {
    display: flex;
    align-items: flex-start;
    gap: .6rem;
    padding: .4rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.03);
    font-size: .88rem;
  }
  .item:last-child { border-bottom: none; }
  .item-icon { flex-shrink: 0; width: 1.1rem; text-align: center; }
  .item-text { flex: 1; }
  .item-meta { color: var(--muted); font-size: .8rem; }
  code {
    font-family: var(--mono);
    font-size: .82em;
    background: rgba(255,255,255,0.07);
    padding: .1em .35em;
    border-radius: 4px;
    color: var(--accent);
  }
  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }
  .repos-touched { font-size: .82rem; color: var(--muted); margin-bottom: .9rem; }
  .repos-touched code { color: var(--muted); }
  footer { text-align: center; color: var(--muted); font-size: .8rem; margin-top: 3rem; }
</style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <div class="report-header">
    <h1>📊 Weekly Team Report</h1>
    <div style="color:var(--muted)">
      <strong style="color:var(--text)">{{ report.org }}</strong> &nbsp;·&nbsp;
      {{ report.week_start.strftime('%B %d') }} – {{ report.week_end.strftime('%B %d, %Y') }}
    </div>
    <div class="meta-grid">
      <div class="meta-card">
        <span class="num">{{ report.developers|length }}</span>
        <span class="label">Active Devs</span>
      </div>
      <div class="meta-card">
        <span class="num">{{ report.total_commits }}</span>
        <span class="label">Commits</span>
      </div>
      <div class="meta-card">
        <span class="num">{{ report.total_prs }}</span>
        <span class="label">Pull Requests</span>
      </div>
      <div class="meta-card">
        <span class="num">{{ report.total_tasks }}</span>
        <span class="label">Tasks Done</span>
      </div>
    </div>
  </div>

  <!-- Summary Table -->
  <div class="section">
    <h2>Summary</h2>
    <table>
      <thead>
        <tr>
          <th>Developer</th>
          <th style="text-align:center">Commits</th>
          <th style="text-align:center">PRs</th>
          <th style="text-align:center">Merged</th>
          <th style="text-align:center">Tasks</th>
        </tr>
      </thead>
      <tbody>
        {% for dev in report.developers %}
        <tr>
          <td><strong>{{ dev.display_name }}</strong><br><span style="font-family:monospace;font-size:.8rem;color:var(--muted)">{{ dev.login }}</span></td>
          <td class="num">{{ dev.commit_count }}</td>
          <td class="num">{{ dev.pr_count }}</td>
          <td class="num">{{ dev.merged_pr_count }}</td>
          <td class="num">{{ dev.task_count }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <!-- Developer Breakdown -->
  <div class="section">
    <h2>Developer Breakdown</h2>

    {% for dev in report.developers %}
    <div class="dev-card">
      <div class="dev-card-header">
        <div>
          <div class="dev-name">{{ dev.display_name }}</div>
          <div class="dev-login">@{{ dev.login }}</div>
        </div>
        <div class="dev-stats">
          <span class="stat-pill"><span>{{ dev.commit_count }}</span> commits</span>
          <span class="stat-pill"><span>{{ dev.pr_count }}</span> PRs</span>
          <span class="stat-pill"><span>{{ dev.task_count }}</span> tasks</span>
        </div>
      </div>
      <div class="dev-body">

        {% if dev.repos_touched %}
        <div class="repos-touched">
          Repos: {% for r in dev.repos_touched %}<code>{{ r }}</code>{% if not loop.last %}, {% endif %}{% endfor %}
        </div>
        {% endif %}

        {% if dev.commits %}
        <div class="sub-section">
          <div class="sub-title">Commits</div>
          {% for c in dev.commits|sort(attribute='authored_at', reverse=True) %}
          <div class="item">
            <span class="item-icon">📝</span>
            <div class="item-text">
              <a href="{{ c.url }}" target="_blank"><code>{{ c.sha }}</code></a>
              {{ c.message }}
              <div class="item-meta"><code>{{ c.repo }}</code> · {{ c.authored_at.strftime('%b %d') }}</div>
            </div>
          </div>
          {% endfor %}
        </div>
        {% endif %}

        {% if dev.pull_requests %}
        <div class="sub-section">
          <div class="sub-title">Pull Requests</div>
          {% for pr in dev.pull_requests|sort(attribute='created_at', reverse=True) %}
          <div class="item">
            <span class="item-icon">
              {% if pr.state == 'merged' %}🟣{% elif pr.state == 'open' %}🟢{% else %}🔴{% endif %}
            </span>
            <div class="item-text">
              <a href="{{ pr.url }}" target="_blank">#{{ pr.number }} {{ pr.title }}</a>
              <span class="badge badge-{{ pr.state }}">{{ pr.state }}</span>
              <div class="item-meta"><code>{{ pr.repo }}</code> · {{ pr.created_at.strftime('%b %d') }}</div>
            </div>
          </div>
          {% endfor %}
        </div>
        {% endif %}

        {% if dev.trello_cards %}
        <div class="sub-section">
          <div class="sub-title">Completed Tasks</div>
          {% for card in dev.trello_cards|sort(attribute='last_activity', reverse=True) %}
          <div class="item">
            <span class="item-icon">✅</span>
            <div class="item-text">
              <a href="{{ card.url }}" target="_blank">{{ card.name }}</a>
              <div class="item-meta">{{ card.board_name }} / {{ card.list_name }} · {{ card.last_activity.strftime('%b %d') }}</div>
            </div>
          </div>
          {% endfor %}
        </div>
        {% endif %}

      </div>
    </div>
    {% endfor %}
  </div>

  <footer>Generated automatically · {{ report.week_range }}</footer>
</div>
</body>
</html>"""


def render_html(report: WeeklyReport) -> str:
    env = Environment(loader=BaseLoader())
    tmpl = env.from_string(_TEMPLATE)
    return tmpl.render(report=report)
