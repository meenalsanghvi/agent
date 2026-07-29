"""Phase 6 — final catalogue diff and blast-radius check.

Two questions, and the second is the important one:

  1. Did the catalogue change the way we intended?  (+15 merged, -39 retired)
  2. Did we damage anything belonging to another team?

Check 2 is the one that would have caught the previous incident. The columnMetadata
clobber did NOT remove reports from the catalogue -- it silently emptied their COLUMNS,
because a column is served only when its filterTags intersect its report's. A report can
therefore still be listed while having lost half its attributes. So we compare the
attribute/metric KEY SETS of every non-ours report against the snapshot, not just the
list of report names.

Usage: HTTP_PROXY= HTTPS_PROXY= NO_PROXY="*" python3 final_catalogue_diff.py --dir <snapshot>
"""

import argparse
import json
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE = "http://test.onlinesales.ai"
APP = "irisTestApplication"
H = {"Content-Type": "application/json"}
S = requests.Session()
S.trust_env = False


def merged_external_types():
    out = set()
    for wave in ("merge_wave1", "merge_wave2", "merge_wave3"):
        out |= {s["externalReportType"] for s in __import__(wave).SPECS}
    return out


def index(reports):
    return {r["externalReportType"]: r for r in reports}


def keysets(rep):
    return (set((rep.get("attributes") or {}).keys()),
            set((rep.get("metrics") or {}).keys()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    a = ap.parse_args()

    before = index(json.load(open(os.path.join(a.dir, "catalogue_baseline.json")))["reports"])
    r = S.get(f"{BASE}/kamService/report/config/external",
              params={"application": APP}, headers=H, timeout=90)
    if r.status_code != 200:
        sys.exit(f"FATAL: catalogue GET {r.status_code}")
    after = index(r.json().get("reports", []))

    ours = merged_external_types()
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))

    print(f"catalogue: {len(before)} → {len(after)}")
    print(f"\nADDED ({len(added)}):")
    for n in added:
        print(f"  {'ours ' if n in ours else 'OTHER'}  {n}")
    print(f"\nREMOVED ({len(removed)}):")
    for n in removed:
        print(f"  {n}")

    # ---- blast radius: every report that is not one of ours must be untouched ----
    print("\n" + "=" * 90)
    print("BLAST-RADIUS CHECK — non-ours reports must be byte-identical in their column sets")
    damaged, checked = [], 0
    for name, rep_before in sorted(before.items()):
        if name in ours:
            continue
        rep_after = after.get(name)
        if rep_after is None:
            if name in removed:
                continue  # accounted for below
            damaged.append((name, "VANISHED"))
            continue
        checked += 1
        ab, mb = keysets(rep_before)
        aa, ma = keysets(rep_after)
        if ab != aa or mb != ma:
            damaged.append((name, f"attrs -{sorted(ab - aa)} +{sorted(aa - ab)} | "
                                  f"metrics -{sorted(mb - ma)} +{sorted(ma - mb)}"))

    unexpected_removals = [n for n in removed if n in ours]
    print(f"  non-ours reports checked: {checked}")
    if damaged:
        print(f"\n❌ {len(damaged)} NON-OURS REPORTS CHANGED — this is a P0:")
        for n, why in damaged:
            print(f"    {n}: {why}")
    if unexpected_removals:
        print(f"\n❌ our own merged reports missing from the catalogue: {unexpected_removals}")

    ok = not damaged and not unexpected_removals
    print(f"\n{'✅ SAFE — no other team' + chr(39) + 's report changed.' if ok else '❌ UNSAFE — restore from snapshot.'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
