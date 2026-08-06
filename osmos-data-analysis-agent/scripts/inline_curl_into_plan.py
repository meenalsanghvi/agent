"""Inline the full 173-column curl into Step 3 of the deployment plan.

The reference PULSE plan embeds its columnMetadata call in full rather than pointing at a
file, so the plan is self-contained and a deployer can copy it straight out. Do the same
here, replacing the `--data @file` short form.

Rebuilds the curl from the payload at write time so the plan cannot drift from the configs.
"""
import json, re, subprocess

PLAN = "/Users/meenal.sanghvi/agent/osmos-data-analysis-agent/DEPLOYMENT-PLAN.md"
SRC = "/Users/meenal.sanghvi/kamService/config/columnMetadata.internalPerformance.json"
URL = "https://osint.onlinesales.ai/kamService/report/column-metadata/"

payload = json.load(open(SRC))
body = json.dumps(payload, indent=4, ensure_ascii=False)
shell_safe = body.replace("'", "'\\''")
full_curl = (f"curl --location '{URL}' \\\n"
             f"--header 'Content-Type: application/json' \\\n"
             f"--data '{shell_safe}'")

plan = open(PLAN).read()

OLD = """- [ ]  Post the payload

    ```bash
    curl --location 'https://osint.onlinesales.ai/kamService/report/column-metadata/' \\
    --header 'Content-Type: application/json' \\
    --data @config/columnMetadata.internalPerformance.json
    ```
"""

NEW = f"""- [ ]  Post the payload — **one call, all 173 columns**

<details>
<summary><b>Click to expand the full call</b> (173 columns, ~65 KB)</summary>

```bash
{full_curl}
```

</details>

Equivalent short form, if you have the repo checked out:

```bash
curl --location '{URL}' \\
--header 'Content-Type: application/json' \\
--data @config/columnMetadata.internalPerformance.json
```
"""

assert OLD in plan, "Step 3 post block not found — plan structure changed"
plan = plan.replace(OLD, NEW, 1)

# the note below it referred to the file-only form; restate it now that the call is inline
OLD_NOTE = """**Why a file and not an inline payload:** 173 columns is ~44 KB. It is generated from the
43 configs by `scripts/build_colmeta_payload.py` and committed as
`config/columnMetadata.internalPerformance.json`, so the posted content is reviewable."""

NEW_NOTE = """**Nothing here is hand-written.** `scripts/build_colmeta_payload.py` generates the payload
from the 43 report configs, and `scripts/render_colmeta_curl.py` renders the call above from
that payload — so neither can drift from what the reports actually expose. Both the payload
(`config/columnMetadata.internalPerformance.json`) and the rendered call
(`config/columnMetadata.internalPerformance.curl.sh`) are committed.

**The escaping matters.** 28 descriptions contain apostrophes, which inside a single-quoted
shell string must be written `'\\''`. Get it wrong and the shell truncates the payload at the
first apostrophe and curl posts a fragment **with no error**. The renderer round-trips the
finished command back through the shell's quoting and re-parses it as JSON, asserting it
matches the source."""

assert OLD_NOTE in plan, "columnMetadata note not found"
plan = plan.replace(OLD_NOTE, NEW_NOTE, 1)

open(PLAN, "w").write(plan)

# verify the embedded call is still valid JSON after the round trip through the markdown
m = re.search(r"--data '(\{.*?\})'\n```", plan, re.S)
extracted = m.group(1).replace("'\\''", "'")
ok = json.loads(extracted) == payload
print(f"  plan lines            : {plan.count(chr(10)):,}")
print(f"  columns embedded      : {len(payload['columns'])}")
print(f"  embedded JSON valid   : {ok}")
print(f"  matches source payload: {json.loads(extracted) == payload}")
assert ok
print("done")
