"""
KAM Service Client
==================
Wraps osSvcClient4pyV2's KamServiceClient for report fetching.
Mirrors osmos-reporting-mcp's KAMClient, plus a `fetch_agent_report` helper that
builds the payload for our fixed KAM_AGENT_* reports (comparison-aware).
"""
from __future__ import annotations

import logging

from osSvcClient4pyV2.kam_svc_client import KamServiceClient

from ..config.settings import settings

logger = logging.getLogger(__name__)


class KAMClient:
    """Client for KAM reporting endpoints via osSvcClient4pyV2."""

    def __init__(self, app_name: str = None, env_domain: str = None):
        self._client = KamServiceClient(
            app_name=app_name or settings.APP_NAME,
            env_domain=env_domain or settings.KAM_ENV_DOMAIN or settings.ENV_DOMAIN,
        )

    # ── raw fetch (same surface as osmos-reporting-mcp) ──────────────────

    def fetch_catalog(self, json_query: dict | None = None) -> dict:
        """GET /report/config/external — discover available reports."""
        return self._client.fetch_kam_report_config_external(json_query or {})

    def fetch_report(self, payload: dict, entity_type: str, fetch_mode: str = "client_or_agency") -> dict:
        """Fetch report data via the endpoint appropriate for this fetch_mode.

        fetch_mode:
            "client_or_agency" — /report/fetch/client for CLIENT entities, /report/fetch otherwise.
            "entity_custom"    — /report/fetch/entity/custom, keyed by entityId/entityType.
        """
        if fetch_mode == "entity_custom":
            return self._client.fetch_kam_entity_custom_report(payload)
        if entity_type == "CLIENT":
            return self._client.fetch_kam_report_client(payload)
        return self._client.fetch_kam_report(payload)

    # ── agent helper: build the payload for a fixed KAM_AGENT_* report ───

    def fetch_agent_report(
        self,
        report_type: str,
        agency_id: int,
        date_ranges: list[dict],
        metrics: list[str],
        attributes: list[str] | None = None,
        filters: list[dict] | None = None,
        entity_type: str = "AGENCY",
        entity_id: int | None = None,
        limit: int = 100000,
        offset: int = 0,
    ) -> list[dict]:
        """Fetch one KAM_AGENT_* report and return its `data` rows.

        `date_ranges` is [{"startDate","endDate"}, ...] — pass two for comparison
        mode (current + baseline). Uses INTERNAL column names (useExternalNames
        False) since the KAM_AGENT_* configs are internal to the agent.
        """
        payload = {
            "agencyId": agency_id,
            "reportType": report_type,
            "requestType": "REPORTING",
            "useExternalNames": False,
            "attributes": attributes or [],
            "metrics": metrics,
            "dateRanges": date_ranges,
            "filters": filters or [],
            "limit": limit,
            "offset": offset,
        }
        if entity_type == "CLIENT" and entity_id is not None:
            payload["clientId"] = entity_id

        result = self.fetch_report(payload, entity_type)
        return result.get("data", []) if isinstance(result, dict) else []
