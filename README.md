# Readwise Reader Recommendation Engine

A personalized reading recommendation engine that analyzes your [Readwise Reader](https://readwise.io/read) backlog and surfaces the most relevant articles daily via email. Powered by [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview)'s multi-agent architecture.

Inspired by [Paperboy](https://www.joshbeckman.org/blog/practicing/building-paperboy-a-personal-reading-recommendation-engine) by Josh Beckman.

## The Problem

If you're a heavy Readwise Reader user, you probably have 200+ articles saved in your inbox. Reading them randomly doesn't create "flow" — you need recommendations that are **relevant to what you're working on right now** to maintain momentum. Standard approaches (chronological, tags, search, random) don't cut it.

## The Solution

This engine uses a **multi-agent AI system** that:

1. **Understands your current focus** — what you're working on, learning, and curious about
2. **Analyzes your reading patterns** — what you've been reading recently, favorite authors, trusted sources
3. **Matches articles holistically** — finds articles at the *intersection* of both signals
4. **Delivers via email** — styled HTML email with relevance explanations and direct Reader links

The best recommendations sit at the intersection of multiple signals. An article that matches *both* your current focus *and* continues your reading patterns is more valuable than one matching only a single signal.

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│  TRIGGER: run.sh (cron / launchd / manual)                      │
│  claude -p "Use readwise-recommender skill"                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Data Collection                                        │
│  fetch_readwise.py → data/new.md, data/later.md, data/recent.md│
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Parallel Analysis (2 Claude Subagents)                 │
│                                                                 │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│  │  current-focus-analyst  │  │  reading-patterns-analyst   │  │
│  │                         │  │                              │  │
│  │  Reads current_focus.md │  │  Reads data/recent.md       │  │
│  │  → themes, goals,      │  │  → patterns, trends,        │  │
│  │    interests            │  │    favorite sources          │  │
│  └─────────────────────────┘  └─────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Unified Matching (Main Orchestrator - SKILL.md)        │
│  Reads both analyses + inbox articles → selects recommendations │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Email Delivery                                         │
│  send_email.py → Styled HTML email via Resend API               │
└─────────────────────────────────────────────────────────────────┘
```

### Recommendation Categories

Each daily email contains:

| Category | Count | Description |
|----------|-------|-------------|
| Must Read | 2-3 | High relevance, quick reads (under 15 mins) |
| Deep Dive | 1 | Very high relevance, longer read (15+ mins) |
| Video Pick | 1 | Relevant YouTube video from your inbox |
| Interesting Connections | 2 | Serendipitous — unexpected but valuable |
| Last Week's Reading | 5 | Recently archived articles (for motivation) |

Every recommendation includes a personalized **"Why"** explanation — not just "related to AI" but specific connections like *"Directly addresses the vLLM routing optimization you're working on. Covers prefill/decode disaggregation which is exactly what you need."*

## Project Structure

```
.
├── .claude/
│   ├── agents/
│   │   ├── current-focus-analyst.md    # Subagent: analyzes your current focus
│   │   └── reading-patterns-analyst.md # Subagent: analyzes reading patterns
│   └── skills/
│       └── readwise-recommender/
│           ├── SKILL.md                # Main orchestrator (coordinates workflow)
│           └── scripts/
│               ├── fetch_readwise.py   # Fetches articles from Readwise API
│               └── send_email.py       # Sends styled email via Resend API
├── current_focus.md                    # Your current interests (edit this!)
├── run.sh                              # Entry point for automation
├── viewer.html                         # Log viewer for debugging runs
├── architecture.md                     # Detailed architecture & design decisions
├── CLAUDE.md                           # Project context for Claude
├── .env.example                        # Environment variables template
└── .gitignore
```

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) CLI installed
- [uv](https://docs.astral.sh/uv/) (Python package manager) installed
- [Readwise Reader](https://readwise.io/read) account with API access
- [Resend](https://resend.com) account for email delivery (free tier: 100 emails/day)

## Setup

### 1. Clone and configure

```bash
git clone https://github.com/Gladiator07/readwise-reader-recommendation-engine.git
cd readwise-reader-recommendation-engine

# Set up environment variables
cp .env.example .env
# Edit .env with your actual values
```

### 2. Get your API tokens

- **Readwise Token**: Go to [readwise.io/access_token](https://readwise.io/access_token)
- **Resend API Key**: Sign up at [resend.com](https://resend.com), create an API key

### 3. Edit your current focus

Edit `current_focus.md` with your current projects, learning goals, and interests:

```markdown
## Work
- Building an LLM inference router with vLLM
- Writing technical blog posts about speculative decoding

## Learning
- Distributed training fundamentals
- Attention mechanism deep-dives

## Leisure / Curiosity
- Productivity systems and note-taking workflows
```

### 4. Run

```bash
# Manual run
./run.sh

# Or invoke the skill directly
claude -p "Use the readwise-recommender skill"
```

### 5. Schedule (optional)

#### macOS (launchd — recommended)

launchd runs missed jobs when your Mac wakes up (unlike cron which just skips them):

```bash
# Create the plist
cat > ~/Library/LaunchAgents/com.user.readwise-recommender.plist << 'EOF'
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
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
EOF

# Enable
launchctl load ~/Library/LaunchAgents/com.user.readwise-recommender.plist
```

#### Linux (cron)

```bash
# Run daily at 8am
0 8 * * * cd /path/to/readwise-reader-recommendation-engine && ./run.sh
```

## Architecture Deep Dive

### Why Multi-Agent?

The key insight is **analyze separately, match holistically**:

| Approach | Pros | Cons |
|----------|------|------|
| Single-pass | Faster, simpler | May miss nuanced connections |
| Each agent recommends | More diverse | Duplicates, fragmented view |
| **Analyze then match** | Holistic view, finds intersections | Slightly more complex |

Two specialized subagents focus on deep analysis of their domain (current focus vs. reading patterns). The main orchestrator sees all context and makes holistic recommendations at the intersection of both signals.

### Data Flow

1. **`fetch_readwise.py`** hits the Readwise Reader API (`/api/v3/list/`) and exports:
   - `data/new.md` — Inbox articles (primary recommendation pool)
   - `data/later.md` — Later/backlog articles (secondary pool)
   - `data/recent.md` — Archived articles from last 14 days (for pattern analysis)

2. **`current-focus-analyst`** reads `current_focus.md` and produces a natural language analysis of active work, learning goals, leisure interests, and implicit curiosities.

3. **`reading-patterns-analyst`** reads `data/recent.md` and produces a quantitative analysis: recurring topics with counts, favorite authors, trusted domains, and emerging trends.

4. **SKILL.md orchestrator** reads both analyses + all inbox articles, scores each article against both signals, and selects the day's recommendations.

5. **`send_email.py`** renders the recommendations JSON into a styled HTML email (gradient sections, reading times, direct Reader links) and sends via Resend.

### Zero Dependencies Philosophy

Python scripts use [PEP 723 inline dependencies](https://peps.python.org/pep-0723/):

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests>=2.28.0"]
# ///
```

No virtualenv, no pip install — just `uv run script.py` and it handles everything.

### Fresh Data, No Cache

Like Paperboy, every run fetches fresh data from Readwise. No caching, no stale state. Articles change (new saves, archives, tag updates), and recommendations should always reflect the current state.

## Email Preview

The email includes styled sections with gradient backgrounds:

- **Must Read** (blue) — Quick, high-relevance reads with time estimates
- **Deep Dive** (pink) — One significant piece worth focused attention
- **Video Pick** (orange) — Today's video recommendation
- **Interesting Connections** (green) — Serendipitous discoveries
- **Last Week's Reading** (gray) — Your recent reading activity for motivation

Each article links directly to Readwise Reader with an "Open in Reader" button.

## Customization

### Context Sources

The default context source is `current_focus.md`. On macOS, the `current-focus-analyst` agent also supports reading from [Bear](https://bear.app/) notes via the [bear-notes-skill](https://github.com/nichochar/bear-notes-skill) — see the agent file for details.

You can adapt the agent to pull context from any source: Obsidian, Notion, a plain text file, or any API.

### Recommendation Tuning

Edit `.claude/skills/readwise-recommender/SKILL.md` to adjust:
- Number of recommendations per category
- Prioritization rules (recency vs. relevance)
- Category definitions
- Context line style and tone

## Log Viewer

The included `viewer.html` is a browser-based log viewer for debugging runs. Open it in a browser and drop in a log file from `logs/` to see the full Claude conversation — tool calls, agent outputs, and recommendations.

## Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `READWISE_TOKEN` | [Readwise API](https://readwise.io/access_token) authentication | Yes |
| `RESEND_API_KEY` | [Resend](https://resend.com) email API | Yes |
| `RECIPIENT_EMAIL` | Email address to receive recommendations | Yes |
| `SENDER_EMAIL` | Sender email address | No (defaults to `onboarding@resend.dev`) |

## References

- [Paperboy](https://www.joshbeckman.org/blog/practicing/building-paperboy-a-personal-reading-recommendation-engine) by Josh Beckman — Original inspiration
- [Readwise Reader API](https://readwise.io/reader_api) — API documentation
- [Claude Code Skills](https://docs.anthropic.com/en/docs/claude-code/overview) — Skills & agents framework
- [Resend API](https://resend.com/docs) — Email delivery
- [UV Scripts](https://docs.astral.sh/uv/guides/scripts/) — PEP 723 inline dependencies
- [PEP 723](https://peps.python.org/pep-0723/) — Inline script metadata

## License

MIT
