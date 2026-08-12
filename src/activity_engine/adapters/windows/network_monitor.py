"""Windows network/DNS monitor using psutil.

Phase 1 network telemetry uses ``psutil.net_connections`` and
``psutil.net_io_counters`` to observe active remote endpoints.  This provides
real network activity without requiring WinDivert / raw sockets or
administrator rights.
"""

from __future__ import annotations

from typing import Any

import psutil

from ...logging import get_logger

logger = get_logger("activity_engine.network", component="NETWORK", event="SCAN")

class WindowsNetworkMonitor:
    """Real Windows network monitor backed by psutil."""

    def __init__(self) -> None:
        self.started = False
        self._seen: dict[str, float] = {}

    async def start(self) -> None:
        self.started = True
        logger.info(
            "backend=psutil status=READY",
            event="INIT",
            component="NETWORK",
        )

    async def stop(self) -> None:
        self.started = False

    async def get_recent_domains(self) -> list[dict[str, Any]]:
        """Return active remote endpoints (host, port) as pseudo-domains.

        psutil exposes remote IP addresses rather than DNS names.  For safety
        and determinism we emit the literal ``ip:port`` string without
        performing reverse DNS (which can block and leaks internal hostnames).
        The policy engine can still match on these stable endpoint labels.
        """
        domains: list[dict[str, Any]] = []
        try:
            for conn in psutil.net_connections(kind="inet"):
                if conn.status != "ESTABLISHED" or conn.raddr is None:
                    continue
                ip, port = conn.raddr
                host = f"{ip}:{port}"
                if host not in self._seen:
                    self._seen[host] = 1.0
                    domains.append({"domain": host, "protocol": "tcp"})
            logger.debug(
                "new=%d",
                len(domains),
                event="SCAN",
                component="NETWORK",
            )
        except (psutil.AccessDenied, psutil.NoSuchProcess) as exc:
            logger.warning(
                "error_type=%s message=%s",
                exc.__class__.__name__,
                exc,
                event="ERROR",
                component="NETWORK",
            )
        return domains
