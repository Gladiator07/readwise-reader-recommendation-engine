#!/bin/bash
set -e

# Change to script directory
cd "$(dirname "$0")"

# Source and EXPORT environment variables (so child processes inherit them)
if [ -f .env ]; then
    set -a  # automatically export all variables
    source .env
    set +a
fi

# --- "Already ran today" check (for launchd reliability) ---
TIMESTAMP_FILE="logs/.last_run_date"
TODAY=$(date +%Y-%m-%d)

if [ -f "$TIMESTAMP_FILE" ]; then
    LAST_RUN=$(cat "$TIMESTAMP_FILE")
    if [ "$LAST_RUN" = "$TODAY" ]; then
        echo "Already ran today ($TODAY). Exiting."
        exit 0
    fi
fi

echo "Running Personalized Readwise Reading Recommender (headless)..."

# Ensure logs directory exists
mkdir -p logs

LOG_FILE="logs/run-$(date +%Y%m%d-%H%M%S).log"

claude -p "Use the readwise-recommender skill to generate today's reading recommendations and send via email" \
    --allowedTools "Bash,Read,Write,Edit,Skill,Task,Glob" \
    --verbose \
    --output-format stream-json \
    | tee "$LOG_FILE"

# Record successful run
echo "$TODAY" > "$TIMESTAMP_FILE"

echo ""
echo "Log saved to: $LOG_FILE"
echo "Done!"
