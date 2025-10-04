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
RUN_STATUS=$(echo "$RUN_JSON" | grep -m 1 '"status"' | awk -F '"' '{print $4}')
RUN_CONCLUSION=$(echo "$RUN_JSON" | grep -m 1 '"conclusion"' | awk -F '"' '{print $4}')
RUN_URL=$(echo "$RUN_JSON" | grep -m 1 '"html_url"' | awk -F '"' '{print $4}')

echo "📦 Latest Run ID: $RUN_ID"
echo "   Status: $RUN_STATUS"
echo "   Conclusion: ${RUN_CONCLUSION:-pending}"
echo "   URL: $RUN_URL"

if [[ "$RUN_STATUS" != "completed" ]]; then
  echo "⏳ Run is still in progress, try again later."
  exit 0
fi

echo "📥 Downloading logs..."
curl -sSL -H "$AUTH" -H "Accept: application/vnd.github+json" \
  "$API/actions/runs/$RUN_ID/logs" -o run_logs.zip

rm -rf run_logs
unzip -o run_logs.zip -d run_logs >/dev/null

echo "🔎 Scanning logs for failure indicators..."
FAIL_FOUND=false
PATTERNS="Process completed with exit code|Traceback|Error:|Exception|failed|No module named|ImportError|ModuleNotFoundError|Command not found|Killed|Could not"

for f in $(find run_logs -type f -name "step.txt"); do
  if grep -Eq "$PATTERNS" "$f"; then
    echo "---- $f ----"
    grep -E "$PATTERNS" "$f" | tail -n 10
    FAIL_FOUND=true
  fi
done

if [ "$FAIL_FOUND" = false ]; then
  echo "✅ No obvious failures detected (logs look clean)"
fi
