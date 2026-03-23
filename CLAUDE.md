# Readwise Reader Recommendation Engine

Personalized reading recommendation engine powered by Claude Code's multi-agent architecture. Analyzes your Readwise Reader backlog and current focus to surface relevant articles daily via email.

## How It Works

1. `fetch_readwise.py` exports articles from Readwise Reader (inbox, later, archive)
2. Two subagents analyze context in parallel:
   - `current-focus-analyst`: Reads `current_focus.md` to understand current work/interests
   - `reading-patterns-analyst`: Analyzes recently archived articles for reading patterns
3. Main orchestrator (SKILL.md) matches articles against both signals, selects recommendations
4. `send_email.py` delivers styled recommendations via Resend API

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `READWISE_TOKEN` | Readwise API authentication |
| `RESEND_API_KEY` | Resend email API |
| `RECIPIENT_EMAIL` | Email to send recommendations to |
| `SENDER_EMAIL` | Sender email address (optional) |

## Key Files

- `.claude/skills/readwise-recommender/SKILL.md` - Main orchestrator
- `.claude/agents/current-focus-analyst.md` - Analyzes current focus
- `.claude/agents/reading-patterns-analyst.md` - Analyzes reading patterns
- `current_focus.md` - Your current interests/goals (edit this!)
- `scripts/fetch_readwise.py` - Fetches articles from Readwise API
- `scripts/send_email.py` - Sends styled HTML email via Resend
