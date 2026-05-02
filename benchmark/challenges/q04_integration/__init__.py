"""Q4 Integration & Automation — entry-point parity probe."""

from __future__ import annotations


def list_entry_points() -> dict:
    """Enumerate the three required entry points for Q4 verification.

    The actual existence checks are wired in by the qualification CI job.
    """
    return {
        "cli": "apps.cli.main:app",
        "api": "apps.api.main:app",
        "mcp": "apps.mcp_server.server:server",
    }
