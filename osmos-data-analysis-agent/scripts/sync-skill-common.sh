#!/usr/bin/env bash
#
# Sync the canonical skill common-rules into every skill's references/ folder.
#
# The skills are kept self-contained (each carries its own copy of
# common-rules.md) so they stay portable into a plugin. This script is the
# single source of truth: edit .claude/skill-common-rules.md, then run this.
#
# Usage:
#   scripts/sync-skill-common.sh          # copy canonical -> every skill (default)
#   scripts/sync-skill-common.sh --check  # verify copies match; non-zero exit on drift (CI)
#
set -euo pipefail
shopt -s nullglob

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CANONICAL="$ROOT/.claude/skill-common-rules.md"
SKILLS_DIR="$ROOT/.claude/skills"
TARGET_REL="references/common-rules.md"

if [[ ! -f "$CANONICAL" ]]; then
  echo "ERROR: canonical file not found: $CANONICAL" >&2
  exit 2
fi

mode="sync"
if [[ "${1:-}" == "--check" ]]; then
  mode="check"
elif [[ $# -gt 0 ]]; then
  echo "Usage: $0 [--check]" >&2
  exit 2
fi

drift=0
count=0
for dir in "$SKILLS_DIR"/*/ ; do
  dir="${dir%/}"
  [[ -f "$dir/SKILL.md" ]] || continue   # only real skills (must have a SKILL.md)
  count=$((count + 1))
  name="$(basename "$dir")"
  target="$dir/$TARGET_REL"

  if [[ "$mode" == "check" ]]; then
    if [[ ! -f "$target" ]]; then
      echo "MISSING: $name/$TARGET_REL"
      drift=1
    elif ! cmp -s "$CANONICAL" "$target"; then
      echo "DRIFT:   $name/$TARGET_REL"
      drift=1
    else
      echo "ok:      $name"
    fi
  else
    mkdir -p "$dir/references"
    cp "$CANONICAL" "$target"
    echo "synced:  $name"
  fi
done

if [[ "$count" -eq 0 ]]; then
  echo "WARNING: no skills found under $SKILLS_DIR" >&2
  exit 0
fi

if [[ "$mode" == "check" ]]; then
  if [[ "$drift" -ne 0 ]]; then
    echo "" >&2
    echo "common-rules drift detected. Fix with: scripts/sync-skill-common.sh" >&2
    exit 1
  fi
  echo "All $count skill copies match the canonical common-rules."
else
  echo "Synced canonical common-rules into $count skill(s)."
fi
