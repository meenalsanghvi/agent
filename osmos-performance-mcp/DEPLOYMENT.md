# Deployment — osmos-performance-mcp

A remote **HTTP MCP server** (FastMCP + uvicorn) that exposes the data-analysis
agent's SOP tools. It is built and run **exactly like `osmos-reporting-mcp`** — same
base image, private package registry, container pattern, and per-env deploy. The
one-line ask to infra: **onboard `osmos-performance-mcp` the same way as
`osmos-reporting-mcp`.**

## Runtime shape
- Serves on **`0.0.0.0:8080`** (override via `HOST`/`PORT` env).
- MCP endpoint: **`/osmosPerformanceMcp`**
- Health: **`/osmosPerformanceMcp/health`** · Readiness: `/osmosPerformanceMcp/ready`
- Entrypoint: `python -m osmos_performance_mcp.server`
- Single internal endpoint (marketplace ops analysts + scheduled runs). Not for
  analyst laptops — deploy as a hosted service inside the OS network.

## Network (must reach, no proxy)
- **KAM service** — `/kamService/report/fetch` (data). KAM holds the BigQuery
  creds via `sourceInfo.appKey` (`GCP_BQ_KAM_CREDENTIALS`); **this service needs no
  BQ credentials of its own.**
- **Hades** — service auth (via `osSvcClient4pyV2`) + Redis config lookup.
- **Redis** — rate limiting (config fetched from Hades by `REDIS_APP_KEY`).

## App registration (prerequisite)
Register **`osPerformanceMcp`** as an OS application in each environment so
`osSvcClient4pyV2` can authenticate to KAM/Hades and resolve the Redis app context.
(In `ENV_DOMAIN=test`, `APP_NAME` auto-resolves to `irisTestApplication` — matches
the org test convention.)

## Container build (mirrors reporting-mcp Dockerfile)
Multi-stage; installs deps from the private GCP Artifact Registry using a mounted
gcloud credential.

**Build args:**
| Arg | Purpose |
|---|---|
| `IMAGE_REGISTRY_REGION` | region for the `os-docker-images` base image |
| `PROJECT_ID` | GCP project (e.g. `prj-onlinesales-prod-01`) |
| `PACKAGE_REGISTRY_REGION` | region for the `os-python-packages` index |
| `APP` | app dir name (`osmos-performance-mcp`) |
| `ENV` | sets `ENV_DOMAIN` in the runtime image (`test`/`staging`/`prod`) |

**Build secret:** `gcp_creds` (service-account cred file) — used to `gcloud auth`
and mint an Artifact Registry token for `uv pip install`.

```bash
docker build \
  --build-arg IMAGE_REGISTRY_REGION=<region> \
  --build-arg PROJECT_ID=prj-onlinesales-prod-01 \
  --build-arg PACKAGE_REGISTRY_REGION=<region> \
  --build-arg APP=osmos-performance-mcp \
  --build-arg ENV=staging \
  --secret id=gcp_creds,src=<path-to-sa-creds.json> \
  -t osmos-performance-mcp:staging .
```

> **`uv.lock`** is not committed yet — generate it once in an environment with
> access to the private index (`uv lock`) and commit it, so builds are reproducible.

## Environment variables
Defaults live in `config/settings.py`; `.env.example` lists the common set.

| Var | Default | Notes |
|---|---|---|
| `APP_NAME` | `osPerformanceMcp` | → `irisTestApplication` when `ENV_DOMAIN=test` |
| `ENV_DOMAIN` | `prod` | `test` / `staging` / `prod` (set from the `ENV` build arg) |
| `KAM_ENV_DOMAIN` | `""` | overrides `ENV_DOMAIN` for KAM only (else inherits it) |
| `LOG_LEVEL` | `INFO` | |
| `HOST` / `PORT` | `0.0.0.0` / `8080` | read directly from env |
| `REDIS_APP_KEY` | `OS_MCP_REDIS` | Hades app key for the rate-limit Redis |
| `MAX_DATE_RANGE_DAYS` | `180` | request guardrail |
| `RATE_LIMIT_CALLS` / `RATE_LIMIT_PERIOD` | `60` / `60` | per-user, via Redis |

## Auth (callers)
Tool calls carry an `x-token` header validated via Hades `/authorize`
(`ACLMiddleware`), which sets `user_id`/`user_scope` for rate limiting. Single
internal endpoint → `allowed_entity_types=None`. **Decide the user-auth model** for
the internal analyst tool (which token, whether agency-level ACL applies) with the
platform team.

## Consumer wiring (after deploy)
The org plugin's `.mcp.json` points Claude Code / the Agent SDK at the deployed
URL, e.g.:
```json
{ "mcpServers": { "osmos-performance": {
    "type": "http", "url": "https://<internal-host>/osmosPerformanceMcp",
    "headers": { "x-token": "${OS_TOKEN}" } } } }
```

## Infra checklist
- [ ] `git init` the repo (kept separate from `osmos-data-analysis-agent`) + CI, mirroring `osmos-reporting-mcp`.
- [ ] Generate + commit `uv.lock` (private-index env).
- [ ] Register `osPerformanceMcp` as an OS app in `test` / `staging` / `prod`.
- [ ] Build + deploy the container per env (`ENV` build arg) inside the OS network.
- [ ] Confirm egress to KAM, Hades, Redis.
- [ ] Publish the internal endpoint URL; wire it into the plugin `.mcp.json`.
