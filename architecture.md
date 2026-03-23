# Readwise Reading Recommender - Project Plan

## Quick Start

```bash
# Run recommendations (headless via cron or manual)
cd /path/to/readwise-reader-recommendation-engine
./run.sh

# Or manually trigger
claude -p "Use the readwise-recommender skill to generate today's recommendations"
```

**Architecture**: Skill + Multi-Agent Analysis + Headless Mode

```
.claude/
├── settings.json                    # Tool permissions
├── agents/                          # Analysis subagents
│   ├── current-focus-analyst.md
│   └── reading-patterns-analyst.md
└── skills/
    └── readwise-recommender/
        ├── SKILL.md                 # Main orchestrator
        └── scripts/                 # Python with UV inline deps
            ├── fetch_readwise.py
            └── send_email.py
```

---

## Overview

A personalized reading recommendation engine that analyzes your Readwise backlog and Bear notes to surface relevant articles daily. Inspired by [Paperboy](https://www.joshbeckman.org/blog/practicing/building-paperboy-a-personal-reading-recommendation-engine) by Josh Beckman.

### The Problem

- ~200-250 technical articles saved in Readwise Reader inbox (backlog)
- Articles saved are interesting but reading them randomly doesn't create "flow"
- Need recommendations that are **relevant to current work** to maintain momentum
- Standard approaches (chronological, tags, search, random) don't work well
- Heavy technical articles (45-60 min) mixed with quick reads (5-10 min) - need different contexts

### The Solution

Use a **multi-agent analysis system** to:
1. Analyze your current focus (from Bear notes)
2. Analyze your recent reading patterns (from Readwise archives)
3. Match articles holistically against both signals
4. Deliver via email with relevance explanations

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  TRIGGER: run.sh (cron job, headless)                                   │
│  claude -p "Use readwise-recommender skill" --allowedTools "..."        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 1: Data Collection (Python scripts with UV inline deps)           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  fetch_readwise.py                                                      │
│  ├── Fetches "new" location → data/new/*.json                          │
│  ├── Fetches "later" location → data/later/*.json                      │
│  └── Fetches "archive" (14 days) → data/recent/*.json                  │
│                                                                         │
│  Bear notes skill (existing global skill)                               │
│  └── Fetches "Current Focus" note + recent notes → data/context/       │
│                                                                         │
│  (Fresh fetch every run, no caching - like Paperboy)                    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 2: Parallel Analysis (2 Claude Subagents)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────┐   ┌───────────────────────────────┐ │
│  │  current-focus-analyst        │   │  reading-patterns-analyst     │ │
│  │  (.claude/agents/)            │   │  (.claude/agents/)            │ │
│  │                               │   │                               │ │
│  │  Reads:                       │   │  Reads:                       │ │
│  │  • "Current Focus" Bear note  │   │  • data/recent/*.json         │ │
│  │  • Recent Bear notes (7 days) │   │    (archived articles, 14d)   │ │
│  │                               │   │                               │ │
│  │  Outputs: Natural language    │   │  Outputs: Natural language    │ │
│  │  analysis of themes, goals,   │   │  analysis of patterns,        │ │
│  │  interests, curiosities       │   │  trends, favorite sources     │ │
│  └───────────────────────────────┘   └───────────────────────────────┘ │
│                                                                         │
│  Key: Each agent knows it's part of a recommendation system.            │
│  Outputs are natural language (like Paperboy), not structured JSON.     │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 3: Unified Matching (Main orchestrator in SKILL.md)               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Input:                                                                 │
│  • Analysis from current-focus-analyst                                  │
│  • Analysis from reading-patterns-analyst                               │
│  • Articles from data/new/*.json + data/later/*.json                   │
│                                                                         │
│  For each article, score against:                                       │
│  • Current focus alignment (work, learning, leisure)                    │
│  • Reading pattern continuity (extends recent interests)                │
│  • Serendipity potential (surprising but valuable connection)           │
│                                                                         │
│  Selection:                                                             │
│  • Must Read: 3-5 articles with highest combined relevance              │
│  • Interesting Connections: 2-3 with unexpected/serendipitous value     │
│  • For Later: 2-3 lower priority but still relevant                     │
│                                                                         │
│  Priority: "new" location over "later" location                         │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 4: Email Delivery (Python script)                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  send_email.py (UV inline deps: resend)                                 │
│  • Formats recommendations as HTML email                                │
│  • Hybrid format: relevance categories + reading time estimates         │
│  • Clickable Readwise Reader links                                      │
│  • Sends via Resend API                                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Why Multi-Agent (Paperboy Style)

**Analyze separately, match holistically**:

| Approach | Pros | Cons |
|----------|------|------|
| Single-pass | Faster, simpler | May miss nuanced connections |
| Each agent recommends | More diverse | Duplicates, fragmented view |
| **Analyze then match** ✅ | Holistic view, finds intersections | Slightly more complex |

Key insight: The best recommendations often sit at the **intersection** of multiple signals. An article that matches BOTH your current focus AND continues your reading patterns is more valuable than one that only matches one signal.

---

## Project Structure

```
reading_recommendation_engine/
├── .claude/
│   ├── settings.json                           # Tool permissions for headless
│   │
│   ├── agents/                                 # Project-local subagents
│   │   ├── current-focus-analyst.md            # Analyzes Bear notes context
│   │   └── reading-patterns-analyst.md         # Analyzes recent reading
│   │
│   └── skills/
│       └── readwise-recommender/
│           ├── SKILL.md                        # Main skill (orchestrates workflow)
│           └── scripts/
│               ├── fetch_readwise.py           # Fetch Readwise articles
│               └── send_email.py               # Send via Resend API
│
├── data/                                       # Runtime data (gitignored)
│   ├── new/                                    # Inbox articles (JSON)
│   ├── later/                                  # Later articles (JSON)
│   ├── recent/                                 # Archived articles, 14 days (JSON)
│   └── context/                                # Bear notes export (JSON)
│
├── run.sh                                      # Headless entry point
├── CLAUDE.md                                   # Project context
├── project_plan.md                             # This file
└── .gitignore
```

---

## Files to Create

### 1. `.claude/agents/current-focus-analyst.md`

**Purpose**: Analyze Bear notes to understand current work, learning goals, and interests.

**Key elements**:
- Uses existing Bear notes skill to fetch "Current Focus" note + recent notes
- Provides natural language analysis (like Paperboy's agents)
- Knows it's part of a recommendation system

**Tools**: Read, Bash (for bear.py)

**Example output** (natural language):
> Based on the Current Focus note and recent Bear notes, here are the key themes:
>
> **Active Work**: Building an LLM router with vLLM, writing about EAGLE-3 speculative decoding for E2E Networks blog, exploring Claude Code MCP integrations.
>
> **Learning Goals**: Deeper understanding of quantization techniques (GPTQ, AWQ), GPU benchmarking methodologies.
>
> **Leisure Interests**: Productivity systems, note-taking workflows, mechanical keyboards.
>
> **Implicit Curiosities**: Based on recent notes, there's emerging interest in inference optimization patterns and developer tooling...

### 2. `.claude/agents/reading-patterns-analyst.md`

**Purpose**: Analyze recently archived Readwise articles to find reading patterns and trends.

**Key elements**:
- Reads data/recent/*.json (archived articles from last 14 days)
- Identifies patterns, favorite sources, emerging interests
- Provides natural language analysis

**Tools**: Read, Glob

**Example output** (natural language):
> Analysis of 23 articles archived in the last 14 days:
>
> **Recurring Topics**: LLM inference optimization (7 articles), Claude/Anthropic API usage (5 articles), developer productivity tools (4 articles).
>
> **Favorite Authors**: Simon Willison appears 3 times, Chip Huyen twice.
>
> **Trusted Domains**: arxiv.org, simonwillison.net, huggingface.co blog.
>
> **Emerging Interests**: Speculative decoding has appeared in 4 recent reads - this seems to be a growing focus area. MCP servers also appearing more frequently.
>
> **Reading Momentum**: Increasing engagement with Claude Code content, decreasing interest in generic AI news...

### 3. `.claude/skills/readwise-recommender/SKILL.md`

**Purpose**: Main orchestrator skill that coordinates the entire workflow.

**Frontmatter**:
```yaml
---
name: readwise-recommender
description: This skill generates personalized reading recommendations from your
  Readwise inbox based on your current focus and reading patterns. Use when running
  the daily recommendation engine or generating reading recommendations.
---
```

**Workflow**:
1. Run `uv run scripts/fetch_readwise.py` to export articles to data/
2. Spawn current-focus-analyst subagent (reads Bear notes via skill)
3. Spawn reading-patterns-analyst subagent (reads data/recent/)
4. Read both natural language analyses + all inbox articles
5. Match articles against both analyses, select recommendations
6. Generate HTML email with recommendations
7. Run `uv run scripts/send_email.py` to send

### 4. `.claude/skills/readwise-recommender/scripts/fetch_readwise.py`

**UV inline dependencies** (PEP 723):
```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests>=2.28.0"]
# ///
```

**Functionality**:
- Fetches from Readwise API: new, later, archive (14 days)
- Exports to JSON files with minimal fields: title, author, summary, tags, url, domain, word_count
- Fresh fetch every run (deletes old data first, like Paperboy)
- Extracts domain from URL

**Run with**: `uv run fetch_readwise.py`

### 5. `.claude/skills/readwise-recommender/scripts/send_email.py`

**UV inline dependencies**:
```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["resend>=2.0.0"]
# ///
```

**Functionality**:
- Accepts subject and HTML body as arguments
- Sends via Resend API
- Simple wrapper - the main skill generates the HTML

**Run with**: `uv run send_email.py --subject "Reading Recommendations" --body-file /tmp/email.html`

### 6. `run.sh`

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "Running Readwise Recommender (headless)..."

claude -p "Use the readwise-recommender skill to generate today's reading recommendations and send via email" \
  --allowedTools "Bash,Read,Write,Grep,Glob" \
  --output-format text

echo "Done!"
```

### 7. `CLAUDE.md`

Project context for Claude:
- Purpose: Headless recommendation engine
- Environment variables required: READWISE_TOKEN, RESEND_API_KEY, RECIPIENT_EMAIL
- Data flow overview
- Links to key files

### 8. `.gitignore`

```
data/
*.pyc
__pycache__/
.env
```

---

## Data Sources

### 1. Readwise API

**Endpoint**: `https://readwise.io/api/v3/list/`

**What to fetch**:

| Location | Purpose | Destination |
|----------|---------|-------------|
| `new` | Inbox articles (recommendation pool) | data/new/*.json |
| `later` | Later articles (recommendation pool) | data/later/*.json |
| `archive` | Recently read, 14 days (pattern analysis) | data/recent/*.json |

**Fields to keep per article**:
- title, author, summary, tags, url, word_count
- domain (extracted from URL)

**Fields to remove** (like Paperboy):
- id, created_at, updated_at, notes, html, published_date, source_url, reading_time, category, parent_id

**Why not full content?**
- 250 articles × ~2000 words = 500k words = way too much context
- Title + summary + tags is enough to match interests
- Claude can infer topic from "Building Semantic Routers for LLMs" without reading 2400 words

**Python implementation**:
```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests>=2.28.0"]
# ///

import os
import json
import requests
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime, timedelta

def fetch_reader_documents(location=None, updated_after=None):
    """Fetch documents from Readwise Reader API with pagination."""
    token = os.environ.get('READWISE_TOKEN')
    full_data = []
    next_page_cursor = None

    while True:
        params = {}
        if next_page_cursor:
            params['pageCursor'] = next_page_cursor
        if updated_after:
            params['updatedAfter'] = updated_after
        if location:
            params['location'] = location

        response = requests.get(
            url="https://readwise.io/api/v3/list/",
            params=params,
            headers={"Authorization": f"Token {token}"}
        )
        response.raise_for_status()

        data = response.json()
        full_data.extend(data['results'])

        next_page_cursor = data.get('nextPageCursor')
        if not next_page_cursor:
            break

    return full_data

def extract_domain(url):
    """Extract domain from URL."""
    try:
        return urlparse(url).netloc
    except:
        return "unknown"

def process_article(doc):
    """Keep only relevant fields."""
    return {
        "title": doc.get("title"),
        "author": doc.get("author"),
        "summary": doc.get("summary"),
        "tags": list(doc.get("tags", {}).keys()),
        "url": doc.get("url"),
        "word_count": doc.get("word_count"),
        "domain": extract_domain(doc.get("source_url", ""))
    }
```

### 2. Bear Notes

**Access method**: Use existing global Bear notes skill

```bash
# Search for Current Focus note
python3 ~/.claude/skills/bear-notes-skill/bear.py search "Current Focus" --format json

# Get recent notes (last 7 days)
python3 ~/.claude/skills/bear-notes-skill/bear.py search "@last7days" --format json
```

**What to read**:

| Source | Purpose | Method |
|--------|---------|--------|
| "Current Focus" note | Explicit intent | `search "Current Focus"` |
| Recent notes (7 days) | Implicit interests | `search "@last7days"` |

**Example Current Focus note**:
```markdown
# Current Focus

## Work
- Building LLM router with vLLM semantic routing
- Writing E2E blog about EAGLE-3 speculative decoding
- Exploring Claude Code MCP integrations

## Learning
- Want to go deeper on quantization techniques (GPTQ, AWQ)
- Curious about how other companies do GPU benchmarking

## Fun / Leisure
- Interested in productivity systems and note-taking workflows
- Been wanting to explore mechanical keyboards
```

### 3. Email Delivery (Resend API)

**Service**: [Resend](https://resend.com) - Modern email API

**Why Resend**:
- Simple API (one HTTP POST or Python SDK)
- Generous free tier (100 emails/day)
- Good deliverability
- No SMTP configuration needed
- Works perfectly in headless mode

**Python implementation**:
```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["resend>=2.0.0"]
# ///

import resend
import os

resend.api_key = os.environ["RESEND_API_KEY"]

resend.Emails.send({
    "from": os.environ.get("SENDER_EMAIL", "onboarding@resend.dev"),
    "to": os.environ["RECIPIENT_EMAIL"],
    "subject": f"Reading Recommendations - {date}",
    "html": recommendations_html
})
```

---

## Output Format (Hybrid)

Email structure combining **relevance categories** with **reading times**:

```html
<h1>Reading Recommendations - {date}</h1>
<p><em>Based on: {brief summary of current focus}</em></p>

<hr>

<h2>Must Read</h2>
<p><em>Directly relevant to your current work</em></p>

<h3>1. {Article Title}</h3>
<p><strong>Why:</strong> {1-2 sentence relevance explanation}</p>
<p>⏱ {X} min · <a href="{readwise_url}">Open in Reader</a></p>

<!-- 3-5 articles -->

<hr>

<h2>Interesting Connections</h2>
<p><em>Unexpected but valuable</em></p>

<!-- 2-3 articles with serendipitous value -->

<hr>

<h2>For Later</h2>
<p><em>When you have more time</em></p>

<!-- 2-3 lower priority articles -->

<hr>

<p><small>Archive articles in Readwise after reading.</small></p>
```

**Recommendation categories**:

| Category | Count | Purpose |
|----------|-------|---------|
| Must Read | 3-5 | Highest combined relevance to focus + patterns |
| Interesting Connections | 2-3 | Serendipitous, unexpected value |
| For Later | 2-3 | Lower priority but still relevant |

---

## Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `READWISE_TOKEN` | Readwise API authentication | Yes |
| `RESEND_API_KEY` | Resend email API | Yes |
| `RECIPIENT_EMAIL` | Email to send recommendations to | Yes |
| `SENDER_EMAIL` | Sender email address | Yes |

---

## Execution

### Manual Run

```bash
cd /path/to/readwise-reader-recommendation-engine
./run.sh
```

### Scheduled (launchd - Recommended for macOS)

**Why launchd over cron?**
- If Mac is asleep at scheduled time, launchd runs the job **when Mac wakes up**
- Cron would just miss the job entirely
- Native macOS, better integrated

Create `~/Library/LaunchAgents/com.user.readwise-recommender.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.readwise-recommender</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd /path/to/readwise-reader-recommendation-engine && ./run.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>7</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/readwise-recommender.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/readwise-recommender.log</string>
</dict>
</plist>
```

**Commands**:
```bash
# Load (enable)
launchctl load ~/Library/LaunchAgents/com.user.readwise-recommender.plist

# Unload (disable)
launchctl unload ~/Library/LaunchAgents/com.user.readwise-recommender.plist

# Check status
launchctl list | grep readwise
```

**How it handles sleep**: If your Mac is asleep at 7am, the job runs when it wakes up. You'll get your recommendations when you open your laptop, even if it's 10am.

---

## Implementation Order

1. **Project setup**: Create directory structure, .claude/, CLAUDE.md, .gitignore
2. **fetch_readwise.py**: Implement with UV inline deps, test fetching
3. **current-focus-analyst agent**: Define agent, test with Bear skill
4. **reading-patterns-analyst agent**: Define agent, test with sample data
5. **SKILL.md**: Main orchestrator that coordinates everything
6. **send_email.py**: Email formatting and sending
7. **run.sh**: Headless entry point
8. **Test end-to-end**: Run full workflow manually
9. **Cron setup**: Schedule daily execution

---

## Key Differences from Paperboy

| Aspect | Paperboy | Our System |
|--------|----------|------------|
| Tech stack | Ruby/Rake | Python + UV |
| Context source | MCP blog posts | Bear notes (existing skill) |
| Email delivery | MCP server | Resend API |
| Analysis agents | 3 (writing, reading, journalist) | 2 (focus, patterns) + main orchestrator |
| Project scope | Unclear | Project-local (.claude/) |
| Caching | None (fresh fetch) | None (fresh fetch) |
| Dependencies | Gemfile/Bundler | UV inline (PEP 723) |

---

## Design Decisions

1. **Analyze separately, match holistically**: Subagents focus on deep analysis of their domain. Main orchestrator sees all context and makes holistic recommendations.

2. **UV for dependencies**: Python scripts use PEP 723 inline dependencies for portability. No pip install, no virtualenv - just `uv run script.py`.

3. **Project-local everything**: All agents and skills in .claude/ are project-specific, not global. Portable via git.

4. **Bear skill reuse**: Use existing global Bear notes skill instead of reimplementing SQLite queries.

5. **Hybrid output format**: Combines Paperboy's relevance categories (Must Read, Interesting, For Later) with reading time estimates.

6. **Context-aware subagents**: Each subagent knows it's part of a recommendation system and tailors its analysis output accordingly.

7. **Skills over commands**: Skills are the recommended approach in Claude Code - they're model-invoked and more flexible than slash commands.

---

## Phase 2: State Tracking (Future)

Once MVP is working, add recommendation tracking to prevent repetition:

- Local `state.json` to track recommended articles
- 5-day cooldown before re-recommending
- Flag articles recommended 3+ times for review
- Sync with Readwise archive state (archived = read = done)

---

## References

- [Paperboy by Josh Beckman](https://www.joshbeckman.org/blog/practicing/building-paperboy-a-personal-reading-recommendation-engine) - Original inspiration
- [Readwise Reader API](https://readwise.io/reader_api) - API documentation
- [Resend API](https://resend.com/docs) - Email delivery API documentation
- [UV for Portable Python](https://docs.astral.sh/uv/guides/scripts/) - UV script dependencies
- [PEP 723](https://peps.python.org/pep-0723/) - Inline script metadata
- [Claude Code Skills](https://docs.anthropic.com/en/docs/claude-code) - Skills documentation
