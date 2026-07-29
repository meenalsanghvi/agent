"""Phase 5 — de-list superseded reports from the KAM external catalogue.

KAM has no delete API. The de-list mechanism (reportConfigServiceHelper.js:172): an
update whose body sets a nullable field to null gets that field collected into a Mongo
$unset. Unsetting `externalReportType` removes the report from buildExternalCatalog
(externalConfigServiceHelper.js:15) while leaving the config document intact.

THIS SCRIPT WRITES TO EXISTING MONGO DOCUMENTS. Guards, in order:

  1. The input list comes only from the merge specs' `absorbs` lists.
  2. Every reportType must match ^INTERNAL_PERF_ — otherwise the whole run aborts,
     not just that entry. We never touch a BEAT_/PULSE_/LOCALIUM_/TMP_ report.
  3. An explicit denylist for the infra-blocked audit reports the user is keeping.
  4. Per report: GET by reportType, require EXACTLY ONE document, assert its
     reportType and application match what we intend, and only then write back that
     same document. Never construct a body from scratch, never reuse an id.
  5. Already-unset reports are skipped, not rewritten.

Usage:
  HTTP_PROXY= HTTPS_PROXY= NO_PROXY="*" python3 delist_retired.py --dry-run
  HTTP_PROXY= HTTPS_PROXY= NO_PROXY="*" python3 delist_retired.py --execute
"""

import argparse
import json
import os
import re
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from merge_lib import load  # noqa: E402

BASE = "http://test.onlinesales.ai"
APP = "irisTestApplication"
H = {"Content-Type": "application/json"}
S = requests.Session()
S.trust_env = False

OURS = re.compile(r"^INTERNAL_PERF_")

# Kept deliberately: audit.audit_logs_v2 is unreachable, so neither these nor their
# replacement (AUDIT_EVENTS) could be data-verified. User: "we will verify them later."
DENYLIST = {
    "INTERNAL_PERF_BUDGET_CHANGES",
    "INTERNAL_PERF_CAMPAIGN_STATUS_CHANGES",
    "INTERNAL_PERF_PRODUCT_SELECTION_CHANGES",
}


def targets():
    out = []
    for wave in ("merge_wave1", "merge_wave2", "merge_wave3"):
        for spec in __import__(wave).SPECS:
            for old in spec["absorbs"]:
                if old == spec["path"]:
                    continue
                out.append(load(old)["reportType"])
    return sorted(set(out))


def get_one(rt):
    q = json.dumps({"reportTypes": [rt], "application": APP})
    r = S.get(f"{BASE}/kamService/report/config", params={"jsonQuery": q},
              headers=H, timeout=60)
    if r.status_code != 200:
        return None, f"lookup HTTP {r.status_code}"
    docs = (r.json() or {}).get("reports", [])
    if len(docs) == 0:
        return None, "not found in Mongo"
    if len(docs) > 1:
        return None, f"AMBIGUOUS — {len(docs)} documents match; refusing to guess"
    doc = docs[0]
    if doc.get("reportType") != rt:
        return None, f"lookup returned {doc.get('reportType')!r}, expected {rt!r}"
    if doc.get("application") not in (None, APP):
        return None, f"application mismatch: {doc.get('application')!r}"
    return doc, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--execute", action="store_true")
    a = ap.parse_args()
    if a.execute == a.dry_run:
        sys.exit("pick exactly one of --dry-run / --execute")

    rts = targets()
    rogue = [r for r in rts if not OURS.match(r)]
    if rogue:
        sys.exit(f"ABORT: non-INTERNAL_PERF_ reportTypes in the target list: {rogue}")

    print(f"{len(rts)} retired reportTypes in scope "
          f"({len(DENYLIST & set(rts))} on the keep-denylist)\n")

    todo, skipped = [], []
    for rt in rts:
        if rt in DENYLIST:
            skipped.append((rt, "DENYLIST — infra-blocked, keeping"))
            continue
        doc, why = get_one(rt)
        if doc is None:
            skipped.append((rt, why))
            continue
        if not doc.get("externalReportType"):
            skipped.append((rt, "already de-listed"))
            continue
        eid = doc.get("id") or doc.get("_id")
        if isinstance(eid, dict):
            eid = eid.get("$oid")
        if not eid:
            skipped.append((rt, "no Mongo id on document"))
            continue
        todo.append((rt, eid, doc.get("externalReportType"), doc))

    print(f"WILL DE-LIST ({len(todo)}):")
    for rt, eid, ext, _ in todo:
        print(f"  {rt:48s} id={eid}  unset externalReportType ({ext})")
    if skipped:
        print(f"\nSKIPPED ({len(skipped)}):")
        for rt, why in skipped:
            print(f"  {rt:48s} {why}")

    if a.dry_run:
        print("\n[dry-run] nothing written.")
        return 0

    print(f"\nexecuting — {len(todo)} de-lists, one at a time")
    ok = fail = 0
    for n, (rt, eid, ext, doc) in enumerate(todo, 1):
        # MINIMAL body, deliberately.
        #
        # Do NOT post the document GET returned: /report/config serves a UI projection
        # where `attributes` is [{label, value}], not the selector map. Writing that back
        # would REPLACE each config's real attributes with a label list -- corruption, not
        # a no-op. (Joi rejects it, which is the only reason the first attempt was safe.)
        #
        # buildUpdateQuery only $sets fields present in the body and $unsets nullable
        # fields explicitly set to null, so a minimal body touches nothing else.
        # cacheInfo is the sole unconditionally-required field (config.validator.js:55);
        # it is sent unchanged from the on-disk config.
        body = {"application": APP, "id": eid,
                "cacheInfo": doc.get("cacheInfo") or {"isCachingEnabled": True,
                                                      "cachingExpiryInSec": 900},
                "externalReportType": None}        # → $unset
        r = S.post(f"{BASE}/kamService/report/config",
                   data=json.dumps(body), headers=H, timeout=90)
        good = r.status_code == 200
        ok, fail = ok + good, fail + (not good)
        print(f"  [{n:2d}/{len(todo)}] {rt:48s} {r.status_code}"
              f"{'' if good else ' ' + r.text[:120]}")
        if n % 10 == 0 or n == len(todo):
            g = S.get(f"{BASE}/kamService/report/config/external",
                      params={"application": APP}, headers=H, timeout=60)
            cnt = len((g.json() or {}).get("reports", [])) if g.status_code == 200 else "?"
            print(f"        … catalogue now {cnt} reports")
    print(f"\ndone: {ok} de-listed, {fail} failed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
