#!/usr/bin/env bash
set -euo pipefail

REPO="victorlavrenko/llm-inline-self-scoring"
URL="https://github.com/${REPO}.git"

cd "$(dirname "$0")"

if [ ! -d .git ]; then
  git init -b main
fi

git add -A
if ! git diff --cached --quiet; then
  git commit -m "Release reproducibility package for inline self-scoring paper"
fi

# If the repository already exists, push to it.
if git ls-remote "$URL" >/dev/null 2>&1; then
  if git remote get-url origin >/dev/null 2>&1; then
    git remote set-url origin "$URL"
  else
    git remote add origin "$URL"
  fi
  git push -u origin main
  echo
  echo "Published: https://github.com/${REPO}"
  exit 0
fi

# If GitHub CLI is installed and authenticated, create the public repository automatically.
if command -v gh >/dev/null 2>&1; then
  git remote remove origin >/dev/null 2>&1 || true
  gh repo create "$REPO" --public --source=. --remote=origin --push
  echo
  echo "Published: https://github.com/${REPO}"
  exit 0
fi

cat <<MSG
The local Git repository is ready and committed, but the GitHub repository does not exist yet.

Either install/authenticate GitHub CLI and rerun this script, or create an EMPTY PUBLIC repository named:
  llm-inline-self-scoring
under:
  victorlavrenko

Do not initialize it with README, .gitignore, or license.
Then rerun:
  bash publish_to_github.sh

Expected URL:
  https://github.com/${REPO}
MSG
exit 2
