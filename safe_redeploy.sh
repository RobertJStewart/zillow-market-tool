#!/usr/bin/env bash
set -euo pipefail

# --- Config from env ---
: "${GH_USER:?Set GH_USER}"
: "${GH_TOKEN:?Set GH_TOKEN}"
: "${REPO_NAME:?Set REPO_NAME}"

API="https://api.github.com/repos/${GH_USER}/${REPO_NAME}"
AUTH="Authorization: token ${GH_TOKEN}"

echo "🔎 Quick scan of working tree for token-like strings..."
if git grep -nE 'ghp_[A-Za-z0-9]{36,}' HEAD >/dev/null 2>&1; then
  echo "❌ Potential token-like string found in working tree."
  echo "   Clean files first (remove any real tokens from tracked files) and re-run."
  exit 1
else
  echo "✅ No token-like strings found in working tree."
fi

echo "🔁 Creating orphan branch to rewrite history..."
git checkout --orphan fresh-start
git add -A
git commit -m "Fresh history without secrets"

echo "🧹 Deleting old main (with secret history) and renaming fresh branch..."
git branch -D main || true
git branch -m main

echo "🔗 Resetting remote..."
git remote remove origin 2>/dev/null || true
git remote add origin "https://${GH_TOKEN}@github.com/${GH_USER}/${REPO_NAME}.git"

echo "🚀 Force-pushing clean history to main..."
git push -f origin main

# --- Enable Pages (optional; Pages may auto-enable when gh-pages is published) ---
echo "🌐 Enabling GitHub Pages (if not already)..."
curl -sS -H "${AUTH}" -X POST \
  -H "Accept: application/vnd.github+json" \
  "${API}/pages" \
  -d '{"source":{"branch":"gh-pages","path":"/"}}' || true

# --- Trigger workflow dispatch ---
echo "⚡ Triggering workflow run..."
curl -sS -H "${AUTH}" -X POST \
  -H "Accept: application/vnd.github+json" \
  "${API}/actions/workflows/update.yml/dispatches" \
  -d '{"ref":"main"}'

echo "⏳ Tip: watch the Actions tab for progress."
echo "🌍 Your site will publish to: https://${GH_USER}.github.io/${REPO_NAME}/"
