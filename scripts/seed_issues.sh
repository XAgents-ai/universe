#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v gh >/dev/null || { echo 'GitHub CLI required' >&2; exit 2; }
gh auth status >/dev/null 2>&1 || { echo 'Authenticate first with gh auth login' >&2; exit 2; }
for file in docs/issues/*.md; do
  title=$(head -1 "$file" | sed 's/^# //')
  # Avoid accidental duplicates; exact titles only.
  if gh issue list --state all --limit 100 --json title --jq '.[].title' | grep -Fqx "$title"; then
    echo "Already exists: $title"
  else
    gh issue create --title "$title" --body-file "$file"
  fi
done
