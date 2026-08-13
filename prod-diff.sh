#!/usr/bin/env bash
# Initial version vibe coded

set -euo pipefail

BASE_URL="https://akuli.github.io/electronics-lessons"

# ANSI color codes
YELLOW_TEXT='\033[1;33m'
GREEN_TEXT='\033[1;32m'
RESET='\033[0m'

echo "Comparing local HTML files against GitHub Pages..."

any_diffs=false

# 2. Loop over HTML files directly
for file in *.html */*.html; do
    # Skip if file doesn't exist (extra safety)
    [ -f "$file" ] || continue

    remote_url="${BASE_URL}/${file}"

    # Capture diff output silently
    diff_output=$(diff -u --color=always <(curl -fsL "$remote_url") "$file" || true)

    # Only output if differences were found
    if [ -n "$diff_output" ]; then
        any_diffs=true
        echo -e "\n${YELLOW_TEXT}========================================================================${RESET}"
        echo -e "${YELLOW_TEXT} DIFF: ${file} <---> ${remote_url}${RESET}"
        echo -e "${YELLOW_TEXT}========================================================================${RESET}\n"
        echo "$diff_output"
    fi
done

if [ "$any_diffs" = false ]; then
    echo -e "\n${GREEN_TEXT}All local HTML files match the hosted version on GitHub Pages!${RESET}"
fi
