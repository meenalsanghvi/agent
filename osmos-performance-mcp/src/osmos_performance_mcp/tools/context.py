"""Tool context helpers — read shared instances from the FastMCP lifespan and
normalize KAM comparison rows to the metrics layer's key names."""


def get_kam_client(ctx):
    """Return the shared KAMClient from the lifespan context."""
    return ctx.lifespan_context["kam_client"]


def read_row(row: dict, key_map: dict) -> dict:
    """Rename a single-period KAM row's keys to the metrics-layer names.

    For each {combine_key: kam_key} in key_map, copy row[kam_key] → combine_key
    (missing → 0). KAM does NOT emit comparison variants, so the tool fetches
    current and baseline as separate calls and reads each row with this.
    """
    row = row or {}
    return {combine_key: row.get(kam_key, 0) for combine_key, kam_key in key_map.items()}
