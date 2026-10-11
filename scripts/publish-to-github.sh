#!/usr/bin/env sh
set -eu

# Publish this repository to a GitHub repository that you created yourself.
# Authentication is handled by the user's configured Git/credential manager/SSH.
# Never place access tokens in this script or in the remote URL.

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <git-remote-url>" >&2
  echo "Example: $0 git@github.com:YOUR-ACCOUNT/AEGIS-PRO.git" >&2
  exit 2
fi
REMOTE_URL=$1
case "$REMOTE_URL" in
  https://github.com/* | git@github.com:*) ;;
  *) echo "Refusing non-GitHub or unexpected remote URL. Use https://github.com/... or git@github.com:..." >&2; exit 2 ;;
esac

if ! command -v git >/dev/null 2>&1; then
  echo "git is required but was not found." >&2
  exit 2
fi
cd "$(dirname "$0")/.."
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git init
  git add .
  git commit -m "Initial AEGIS PRO v0.3.0 release"
  git branch -M main
else
  if git rev-parse --verify HEAD >/dev/null 2>&1; then
    if [ -n "$(git status --porcelain)" ]; then
      echo "Working tree has uncommitted changes. Review/commit them before publishing." >&2
      exit 2
    fi
    git branch -M main
  else
    # Allow a freshly initialized repository with no commit yet.
    git add .
    git commit -m "Initial AEGIS PRO v0.3.0 release"
    git branch -M main
  fi
fi

if git remote get-url origin >/dev/null 2>&1; then
  EXISTING=$(git remote get-url origin)
  if [ "$EXISTING" != "$REMOTE_URL" ]; then
    echo "origin already points to a different URL; refusing to replace it." >&2
    echo "Existing: $EXISTING" >&2
    exit 2
  fi
else
  git remote add origin "$REMOTE_URL"
fi

echo "Publishing branch main to $REMOTE_URL"
echo "Make sure the GitHub repository is empty or has no conflicting history."
git push -u origin main
