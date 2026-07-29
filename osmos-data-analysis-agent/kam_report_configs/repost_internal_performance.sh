#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# One-shot re-post of all 63 INTERNAL_PERF_* configs under visibility
# INTERNAL_PERFORMANCE (already set in the files). Updates each config in place
# and re-posts its (merged) columnMetadata — no per-report fetch (--no-fetch).
#
# ⚠️ GATED: run ONLY after kamService's validator change is deployed to the target
# env (INTERNAL_PERFORMANCE added to VALID_VISIBILITY_VALUES). Until then every
# config POST fails Joi validation ("visibility must be one of [...]").
#
# Effect: moves our reports onto the new INTERNAL_PERFORMANCE slice AND removes them
# from the INTERNAL_USER slice — which is what stops them leaking into the
# beatsInternal (prod-Sofie) mount.
#
# Usage:  ./repost_internal_performance.sh [agencyId]      (default 105)
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail
cd "$(dirname "$0")"
AGENCY="${1:-105}"

# ⚠️ `*/` matches EVERY subdirectory, including _retired/. Globbing blindly here
# re-posts the 42 superseded configs and puts them straight back in the external
# catalogue — silently undoing the de-list. This has already happened once.
# Build the list explicitly and refuse to run if anything retired sneaks in.
files=()
for f in */INTERNAL_PERF_*.json; do
  case "$f" in
    _retired/*) continue ;;
  esac
  files+=("$f")
done

if [[ ${#files[@]} -eq 0 ]]; then
  echo "ERROR: no active configs matched — refusing to run" >&2
  exit 2
fi
if printf '%s\n' "${files[@]}" | grep -q '^_retired/'; then
  echo "ERROR: a retired config survived filtering — aborting" >&2
  exit 2
fi

echo "Posting ${#files[@]} active configs (retired excluded)."
echo ""

for f in "${files[@]}"; do
  printf '── %s  ' "$f"
  HTTP_PROXY= HTTPS_PROXY= NO_PROXY="*" python3 post_external.py \
    --config "$f" --agency "$AGENCY" --current 2026-07-19 2026-07-21 --no-fetch 2>&1 \
    | grep -vE "NotOpenSSLWarning|warnings.warn" \
    | grep -E "\[config\]|Invalid request|Error:" | head -1
done

echo ""
echo "Verify (positive — expect our reports):"
echo "  curl -s --noproxy '*' -G '$KAM/kamService/report/config/external' \\"
echo "    --data-urlencode 'jsonQuery={\"visibility\":\"INTERNAL_PERFORMANCE\",\"application\":\"irisTestApplication\"}'"
echo "Verify (negative — expect NONE of ours):"
echo "  ...same with \"visibility\":\"INTERNAL_USER\"  and  \"visibility\":\"BEATS\""
