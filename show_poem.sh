#!/usr/bin/env bash
# Displays today's saved poem-of-the-day file, verbatim (see README.md).
#
# If today's file isn't there yet, tries fetching it on the spot (safe -
# fetch_poem_of_the_day.py is idempotent per day), then falls back to
# showing the most recent poem on file if that doesn't work out.

set -euo pipefail

POEM_DIR="$HOME/poems/poem-of-the-day"
TODAY="$(date +%Y-%m-%d)"
SCRIPT_DIR="$(cd -- "$(dirname -- "$(readlink -f -- "$0")")" && pwd)"
FETCH_SCRIPT="$SCRIPT_DIR/fetch_poem_of_the_day.py"

shopt -s nullglob
today_files=("$POEM_DIR"/"$TODAY"_*.txt)

if [ ${#today_files[@]} -eq 0 ] && [ -f "$FETCH_SCRIPT" ]; then
    timeout 10 python3 "$FETCH_SCRIPT" >/dev/null 2>&1 || true
    today_files=("$POEM_DIR"/"$TODAY"_*.txt)
fi

if [ ${#today_files[@]} -gt 0 ]; then
    cat -- "${today_files[0]}"
    exit 0
fi

all_files=("$POEM_DIR"/*.txt)
if [ ${#all_files[@]} -eq 0 ]; then
    echo "No poems found yet in $POEM_DIR" >&2
    exit 1
fi

latest="$(printf '%s\n' "${all_files[@]}" | sort | tail -n1)"
echo "No poem for today yet - showing the most recent one instead:" >&2
echo >&2
cat -- "$latest"
