---
name: readwise-recommender
description: Generates personalized reading recommendations from your Readwise inbox based on your current focus and reading patterns. Use when running the daily recommendation engine or generating reading recommendations.
---

# Readwise Reading Recommender

This skill generates personalized reading recommendations by:
1. Fetching articles from Readwise Reader
2. Analyzing your current focus (from Bear notes)
3. Analyzing your reading patterns (from recently archived articles)
4. Matching inbox articles against both signals
5. Sending recommendations via email

## Workflow

### Step 1: Fetch Readwise Articles

Run the fetch script to get fresh data:

```bash
uv run .claude/skills/readwise-recommender/scripts/fetch_readwise.py
```

This creates 3 markdown files with article tables:
- `data/new.md` - Inbox articles (recommendation pool)
- `data/later.md` - Later articles (recommendation pool)
- `data/recent.md` - Archived articles from last 14 days (for pattern analysis)

### Step 2: Run Analysis Agents

Spawn BOTH agents in parallel using the Task tool:

1. **current-focus-analyst** - Analyzes Bear notes for current work themes, learning goals, interests
2. **reading-patterns-analyst** - Analyzes `data/recent.md` for reading patterns

Both agents know they are part of a recommendation system and will provide analysis tailored for matching.

### Step 3: Match and Select

After receiving both analyses, read:
- `data/new.md` - Inbox articles
- `data/later.md` - Later articles

#### Identifying Videos vs Articles
- **Videos**: Domain contains `youtube.com` (youtube.com, www.youtube.com, m.youtube.com)
- **Articles**: All other domains

#### Selection Criteria

Select articles into these categories:

| Category | Count | Type | Criteria |
|----------|-------|------|----------|
| 📚 **Must Read** | 2-3 | Articles only | High relevance match, quick reads (under 15 mins each) |
| 🔬 **Deep Dive** | 1 | Article only | Very high relevance, longer read (15+ mins), significant piece |
| 🎬 **Video Pick** | 1 | Video only | Relevant YouTube video from inbox |
| 🔗 **Interesting Connections** | 2 | Articles | Serendipitous - unexpected but potentially valuable |

**Total: 6-7 items per day**

#### Prioritization Rules

1. **Recency matters**: Prefer newer articles over older ones (recently added to inbox)
2. **High match overrides recency**: If an older article is exceptionally relevant, include it
3. **New location over Later**: Prioritize `data/new.md` articles over `data/later.md`
4. **Relevance scoring**: Consider BOTH current focus AND reading patterns for matching

### Step 4: Generate & Save Recommendations as JSON

First create the directory:
```bash
mkdir -p recommendations
```

Write a JSON file to `recommendations/{DD-MM-YYYY}.json` with this structure:

```json
{
  "date": "21-12-2025",
  "context_line": "You're knee-deep in the LLM router project...(2-3 sentences, see guidelines below)",
  "must_read": [
    {
      "title": "Article Title",
      "why": "2-3 sentence explanation of relevance",
      "time": "4 mins",
      "url": "https://read.readwise.io/read/..."
    }
  ],
  "deep_dive": {
    "title": "Article Title",
    "why": "2-3 sentence explanation",
    "time": "15 mins",
    "url": "https://read.readwise.io/read/..."
  },
  "video_pick": {
    "title": "Video Title",
    "why": "2-3 sentence explanation",
    "url": "https://read.readwise.io/read/..."
  },
  "interesting_connections": [
    {
      "title": "Article Title",
      "why": "1-2 sentence explanation",
      "time": "6 mins",
      "url": "https://read.readwise.io/read/..."
    }
  ],
  "last_week": {
    "count": 45,
    "articles": [
      {"title": "Article Title", "url": "https://...", "context": "brief 5-7 word context"},
      {"title": "Article Title", "url": "https://...", "context": "brief context"}
    ]
  }
}
```

**Notes:**
- `must_read`: 2-3 items
- `interesting_connections`: 2 items
- `last_week.articles`: 5 items max
- `video_pick`: No `time` field (videos show "Unknown")
- The send_email.py script will render this JSON into a styled HTML email

#### Writing the Context Line (Header)

The context line sets the stage. Make it **narrative, specific, and 2-3 sentences long**. Paint a picture of what they're working on.

**Good examples:**
- "You're knee-deep in the LLM router project, wrestling with vLLM's prefill/decode routing while simultaneously building Claude Code skills that are already paying off (hello, reading recommender!). On the learning front: distributed training fundamentals and attention mechanism deep-dives. Today's picks hit all these fronts."
- "This week has been all about E2E Networks — writing technical blogs on inference optimization, testing OLMo models in your router, and exploring what makes vLLM tick. You're also leveling up on Claude Code workflows and eyeing distributed training concepts. Here's reading material that matches the intensity."
- "The reading recommender you're building right now? That's peak Claude Code mastery in action. Meanwhile, the LLM router project is pushing you deeper into vLLM internals and inference optimization. And those distributed training resources you bookmarked aren't going to read themselves. Let's fuel all three tracks."

**Bad examples:**
- "Based on: LLM router, Claude Code, distributed training" (just a list, boring)
- "Building the reading recommender, diving into Claude Code workflows..." (too short, not descriptive enough)
- "Based on your interests" (too vague)
- "Here are your recommendations" (no context)

#### Writing Good "Why" Explanations

The "Why" is crucial - it justifies why YOU should read THIS article TODAY.

**Good examples:**
- "Directly addresses the vLLM routing optimization you're working on for E2E Networks. Covers prefill/decode disaggregation which is exactly what you need."
- "You've been exploring Claude Code skills - this is Anthropic's official deep-dive into context engineering for agents."
- "Connects your distributed training learning goals with practical RL implementation using tools you already know."

**Bad examples:**
- "Interesting article about AI" (too vague)
- "Good read" (no context)
- "Related to your interests" (doesn't say how)

#### Building "Last Week's Reading" Section

Use `data/recent.md` (archived articles from last 14 days) to populate `last_week`:
- Show **5 articles** max (pick the most interesting/diverse)
- Count total archived articles for the `count` field
- Keep `context` **very brief** (5-7 words) - just enough to jog memory
- This section is for **motivation**, not deep analysis

### Step 5: Send Email

Send using the JSON file (script renders HTML automatically):

```bash
uv run .claude/skills/readwise-recommender/scripts/send_email.py \
  --subject "📬 Reading Recommendations - $(date +%d-%m-%Y)" \
  --json-file recommendations/{DD-MM-YYYY}.json
```

The script will:
1. Render JSON → HTML using the embedded template
2. Save rendered HTML to `recommendations/{DD-MM-YYYY}.html`
3. Send the email

## Important Notes

- Always run fetch first to get fresh data (no caching)
- Run both analysis agents in PARALLEL for efficiency
- The "Why" explanation is the most important part - be specific and personal
- Prioritize articles at the INTERSECTION of current focus AND reading patterns
- Newer articles > older articles (unless older is exceptionally relevant)
- Don't include `time` field for videos (it shows "Unknown")
- Output JSON only - the send_email.py script handles all HTML rendering

## ⚠️ STRICT WARNING: Bear Notes Access

**DO NOT attempt to access Bear's SQLite database directly under any circumstances.**

The `current-focus-analyst` agent uses a dedicated Bear notes skill (`bear-notes-skill`) to read notes safely. If this skill fails, errors out, or is unavailable:

1. **DO NOT** try to read Bear's database at `~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/database.sqlite`
2. **DO NOT** attempt SQL queries against any Bear database files
3. **DO NOT** try to find alternative paths to Bear's data

Instead:
- Skip the current focus analysis entirely
- Proceed with only the reading patterns analysis from `data/recent.md`
- Note in the email that current focus context was unavailable

Bear's database is protected by macOS permissions. Direct access attempts will trigger security popups and may corrupt the database. The Bear skill handles all this safely - if it doesn't work, accept the limitation and move on.
