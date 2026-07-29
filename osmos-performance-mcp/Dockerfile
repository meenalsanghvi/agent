ARG IMAGE_REGISTRY_REGION
ARG PROJECT_ID

# Stage 1: Install dependencies with uv + GCP keyring auth
FROM ${IMAGE_REGISTRY_REGION}-docker.pkg.dev/${PROJECT_ID}/os-docker-images/python:3.12-slim AS deps

ARG APP
ARG PROJECT_ID
ARG PACKAGE_REGISTRY_REGION

USER root
WORKDIR /usr/local/onlinesales/$APP

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN apt-get update && \
    apt-get install -y curl gnupg lsb-release && \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
    apt-get update && \
    apt-get install -y google-cloud-cli && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN uv venv /venv

COPY pyproject.toml uv.lock ./
RUN --mount=type=secret,id=gcp_creds \
    gcloud auth login --cred-file=/run/secrets/gcp_creds && \
    AR_TOKEN=$(gcloud auth print-access-token) && \
    uv export --no-dev --frozen --no-hashes --no-emit-project > requirements.txt && \
    rm -f pyproject.toml uv.lock && \
    uv pip install --python /venv/bin/python \
        --extra-index-url "https://oauth2accesstoken:${AR_TOKEN}@${PACKAGE_REGISTRY_REGION}-python.pkg.dev/${PROJECT_ID}/os-python-packages/simple/" \
        -r requirements.txt

# Stage 2: Clean runtime image
FROM ${IMAGE_REGISTRY_REGION}-docker.pkg.dev/${PROJECT_ID}/os-docker-images/python:3.12-slim

ARG APP
ARG ENV

USER root
WORKDIR /usr/local/onlinesales/$APP

RUN mkdir -p /etc/onlinesales/ /usr/local/onlinesales/ && \
    groupadd -f onlinesales-dev && \
    useradd -s /bin/bash -G onlinesales-dev -m -d /home/appster appster || true && \
    chown -R appster:appster /etc/onlinesales/ && \
    chown -R appster:appster /usr/local/onlinesales/

COPY --chown=appster:appster src/ ./src/
COPY --chown=appster:appster --from=deps /venv ./src/python

USER appster

ENV ENV_DOMAIN=${ENV}

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s \
  CMD src/python/bin/python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/osmosPerformanceMcp/health')" || exit 1

WORKDIR /usr/local/onlinesales/$APP/src

CMD ["python/bin/python", "-m", "osmos_performance_mcp.server"]
