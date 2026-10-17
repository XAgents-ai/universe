#!/usr/bin/env bash
# Run on YOUR authenticated computer (not from an untrusted hosted notebook).
set -euo pipefail
cd "$(dirname "$0")/.."
NAME="${1:-universe}"
if ! command -v gh >/dev/null; then
  echo 'Install GitHub CLI: https://cli.github.com/' >&2; exit 2
fi
if ! gh auth status >/dev/null 2>&1; then
  echo 'Authenticate interactively first with: gh auth login' >&2; exit 2
fi
if [ ! -d .git ]; then git init -b main; fi
if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git commit -m 'Baseline: Universe V0 R0.3 with collaborative review gates'
fi
if git remote get-url origin >/dev/null 2>&1; then
  echo 'Repository already has origin; refusing to change existing remote.' >&2
  git remote -v
  exit 2
fi
# Creating a PRIVATE remote and pushing the local initial branch is the only remote mutation.
gh repo create "$NAME" --private --source=. --remote=origin --push \
  --description='Evidence-driven persistent digital physical universe for independent agents'
echo ''
echo 'Next: follow docs/GITHUB_SETUP.md to enable protections and model workflows.'
