#!/usr/bin/env bash
set -euo pipefail

: "${GH_USER:?Set GH_USER}"
: "${GH_TOKEN:?Set GH_TOKEN}"
: "${REPO_NAME:?Set REPO_NAME}"

API="https://api.github.com/repos/${GH_USER}/${REPO_NAME}"
AUTH="Authorization: token ${GH_TOKEN}"

echo "🔎 Fetching latest workflow run info..."
RUN_JSON=$(curl -s -H "$AUTH" -H "Accept: application/vnd.github+json" \
  "$API/actions/runs?per_page=1")

RUN_ID=$(echo "$RUN_JSON" | grep '"id"' | head -n 1 | awk '{print $2}' | tr -d ',')
RUN_NAME=$(echo "$RUN_JSON" | grep -m 1 '"name"' | awk -F '"' '{print $4}')
RUN_STATUS=$(echo "$RUN_JSON" | grep -m 1 '"status"' | awk -F '"' '{print $4}')
RUN_CONCLUSION=$(echo "$RUN_JSON" | grep -m 1 '"conclusion"' | awk -F '"' '{print $4}')
RUN_URL=$(echo "$RUN_JSON" | grep -m 1 '"html_url"' | awk -F '"' '{print $4}')

echo "📦 Run ID: $RUN_ID"
echo "   Workflow: $RUN_NAME"
echo "   Status: $RUN_STATUS"
echo "   Conclusion: ${RUN_CONCLUSION:-pending}"
echo "   URL: $RUN_URL"

# If the run hasn't finished, exit early
if [[ "$RUN_STATUS" != "completed" ]]; then
  echo "⏳ Run is still in progress, try again later."
  exit 0
fi

echo "🔎 Fetching job breakdown..."
JOBS_JSON=$(curl -s -H "$AUTH" -H "Accept: application/vnd.github+json" \
  "$API/actions/runs/$RUN_ID/jobs")

echo "$JOBS_JSON" | grep -E '"name"|"status"|"conclusion"'

# Find the failing step, if any
FAILED_STEP=$(echo "$JOBS_JSON" | grep -B2 '"conclusion": "failure"' || true)

if [[ -n "$FAILED_STEP" ]]; then
  echo ""
  echo "❌ Failing step details:"
  echo "$FAILED_STEP"
else
  echo "✅ No failing step detected (conclusion = success)"
fi