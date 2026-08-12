"""CLI entry point for the Activity Engine."""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Any

from .. import __version__


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="activity-engine",
        description="Student Activity Monitoring & Focus Control Engine CLI",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # doctor
    doctor = sub.add_parser("doctor", help="Check system health and capabilities")
    doctor.add_argument("--json", action="store_true", help="Emit JSON report")

    # monitor
    monitor = sub.add_parser("monitor", help="Run live monitoring")
    monitor.add_argument("--poll", type=float, default=3.0, help="Poll interval seconds")
    monitor.add_argument("--mode", choices=["dry_run", "audit_only", "enforce"], default="dry_run")
    monitor.add_argument(
        "--backend",
        choices=["auto", "mock", "real", "extension"],
        default="auto",
        help="auto=pick real monitors on Windows, mock elsewhere; extension=Chrome extension bridge (default: auto)",
    )
    monitor.add_argument(
        "--api-url",
        default="http://127.0.0.1:8000",
        help="Backend base URL for the browser-extension bridge (default: http://127.0.0.1:8000)",
    )

    # simulate
    simulate = sub.add_parser("simulate", help="Replay simulated events")
    simulate.add_argument("--events", type=int, default=10, help="Number of events to simulate")
    simulate.add_argument("--mode", choices=["dry_run", "audit_only", "enforce"], default="dry_run")

    # policy-check
    policy = sub.add_parser("policy-check", help="Validate a policy YAML file")
    policy.add_argument("path", nargs="?", default="config/policy.yaml", help="Path to policy YAML")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "doctor":
        return _cmd_doctor(args)
    if args.command == "monitor":
        return _cmd_monitor(args)
    if args.command == "simulate":
        return _cmd_simulate(args)
    if args.command == "policy-check":
        return _cmd_policy_check(args)
    parser.error(f"Unknown command: {args.command}")
    return 2


# ----------------------------------------------------------------------
# Platform helpers
# ----------------------------------------------------------------------

_IS_WINDOWS = sys.platform.startswith("win")


def _build_monitor_set(backend: str, api_url: str | None = None) -> dict[str, Any]:
    """Build a monitor dict for the requested backend.

    ``real`` is only available on Windows; on other platforms it falls back
    to mocks with a warning so the monitoring loop never crashes.

    ``extension`` uses the Chrome browser-extension bridge on every platform.
    """
    if backend == "extension":
        from ..adapters.extension.browser_monitor import ExtensionBrowserMonitor
        from ..adapters.mock.process_monitor import MockProcessMonitor
        from ..adapters.mock.network_monitor import MockNetworkMonitor

        return {
            "process": MockProcessMonitor(),
            "browser": ExtensionBrowserMonitor(api_url=api_url),
            "network": MockNetworkMonitor(),
        }

    if backend == "real" and not _IS_WINDOWS:
        print("WARNING: --backend real is only supported on Windows; falling back to mocks.")
        backend = "mock"

    if backend == "mock" or not _IS_WINDOWS:
        from ..adapters.mock.process_monitor import MockProcessMonitor
        from ..adapters.mock.browser_monitor import MockBrowserMonitor
        from ..adapters.mock.network_monitor import MockNetworkMonitor

        return {
            "process": MockProcessMonitor(),
            "browser": MockBrowserMonitor(),
            "network": MockNetworkMonitor(),
        }

    # Windows real backend
    from ..adapters.windows.process_monitor import WindowsProcessMonitor
    from ..adapters.windows.network_monitor import WindowsNetworkMonitor
    from ..adapters.mock.browser_monitor import MockBrowserMonitor

    return {
        "process": WindowsProcessMonitor(),
        "browser": MockBrowserMonitor(),
        "network": WindowsNetworkMonitor(),
    }


# ----------------------------------------------------------------------
# Command implementations
# ----------------------------------------------------------------------

def _cmd_doctor(args: argparse.Namespace) -> int:
    """Report system health and available capabilities."""
    report: dict[str, Any] = {
        "version": __version__,
        "platform": sys.platform,
        "python": sys.version.split()[0],
        "checks": [],
    }

    checks = []
    try:
        import psutil  # noqa: F401
        checks.append({"name": "psutil", "ok": True})
    except ImportError:
        checks.append({"name": "psutil", "ok": False, "detail": "psutil not installed"})

    try:
        import yaml  # noqa: F401
        checks.append({"name": "yaml", "ok": True})
    except ImportError:
        checks.append({"name": "yaml", "ok": False, "detail": "PyYAML not installed"})

    try:
        import pydantic  # noqa: F401
        checks.append({"name": "pydantic", "ok": True})
    except ImportError:
        checks.append({"name": "pydantic", "ok": False, "detail": "pydantic not installed"})

    # Screen capture capability (cross-platform).
    try:
        from ..platform.screen import get_screen_provider, default_screenshot_dir

        provider = get_screen_provider()
        monitors = provider.get_monitors()
        checks.append(
            {
                "name": "screen_capture",
                "ok": True,
                "detail": f"monitors={len(monitors)} dir={default_screenshot_dir()}",
            }
        )
    except Exception as exc:  # noqa: BLE001
        checks.append({"name": "screen_capture", "ok": False, "detail": str(exc)})

    # Process monitoring capability (platform-aware).
    try:
        if _IS_WINDOWS:
            from ..adapters.windows.process_monitor import WindowsProcessMonitor

            monitor = WindowsProcessMonitor()
        else:
            from ..adapters.mock.process_monitor import MockProcessMonitor

            monitor = MockProcessMonitor()

        process_ok = True
        checks.append({"name": "process_monitor", "ok": True})
    except Exception as exc:  # noqa: BLE001
        process_ok = False
        checks.append({"name": "process_monitor", "ok": False, "detail": str(exc)})

    # Network monitoring capability (platform-aware).
    try:
        if _IS_WINDOWS:
            from ..adapters.windows.network_monitor import WindowsNetworkMonitor

            net = WindowsNetworkMonitor()
        else:
            from ..adapters.mock.network_monitor import MockNetworkMonitor

            net = MockNetworkMonitor()

        checks.append({"name": "network_monitor", "ok": True})
    except Exception as exc:  # noqa: BLE001
        checks.append({"name": "network_monitor", "ok": False, "detail": str(exc)})

    # Browser extension bridge capability.
    try:
        from ..adapters.extension.browser_monitor import ExtensionBrowserMonitor

        monitor = ExtensionBrowserMonitor()
        checks.append({"name": "browser_extension", "ok": True})
    except Exception as exc:  # noqa: BLE001
        checks.append({"name": "browser_extension", "ok": False, "detail": str(exc)})

    # Device capabilities (best-effort; stubs return capabilities without crashing).
    try:
        from ..adapters.windows.device_controller import WindowsDeviceController

        controller = WindowsDeviceController()
        caps = asyncio.run(controller.get_capabilities())
        checks.append({"name": "device_capabilities", "ok": True, "detail": caps.model_dump()})
    except Exception as exc:  # noqa: BLE001
        checks.append({"name": "device_capabilities", "ok": False, "detail": str(exc)})

    report["checks"] = checks
    all_ok = all(c["ok"] for c in checks)
    report["ok"] = all_ok

    if args.json:
        import json
        print(json.dumps(report, indent=2))
    else:
        print(f"Activity Engine Doctor v{__version__}")
        print(f"  Platform : {sys.platform}")
        print(f"  Python   : {sys.version.split()[0]}")
        for check in checks:
            status = "OK " if check["ok"] else "FAIL"
            detail = check.get("detail", "")
            suffix = f"  ({detail})" if detail else ""
            print(f"  [{status}] {check['name']}{suffix}")
        print("Overall:", "HEALTHY" if all_ok else "ISSUES FOUND")

    return 0 if all_ok else 1


def _cmd_monitor(args: argparse.Namespace) -> int:
    """Run a live monitoring loop using platform-appropriate adapters."""
    from ..config.models import Config, RuntimeConfig, EnforcementMode
    from ..core.decisions import EnforcementMode as DecisionMode
    from ..engine.facade import ActivityEngine
    from ..adapters.mock.action_executor import MockActionExecutor
    from ..services.monitoring_service import MonitoringService

    backend = args.backend
    if backend == "auto":
        backend = "real" if _IS_WINDOWS else "mock"

    config = Config(runtime=RuntimeConfig(mode=DecisionMode(args.mode)))
    engine = ActivityEngine(config=config, executor=MockActionExecutor())
    session_id = engine.start_session()

    monitors = _build_monitor_set(backend, api_url=args.api_url)
    service = MonitoringService(
        event_engine=engine._event_engine,
        monitors=monitors,
        poll_interval_seconds=args.poll,
    )

    print(f"Monitoring started (mode={args.mode}, backend={backend}, session={session_id})")
    if backend == "extension":
        print(f"  Browser source: Chrome extension -> {args.api_url}/api/browser/telemetry")
        print("  NOTE: The backend server must be running for the browser bridge to work.")
    print("Press Ctrl+C to stop.")

    async def _run() -> None:
        await service.start()
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            await service.stop()

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        asyncio.run(service.stop())
        engine.end_session()
        print("\nMonitoring stopped.")
    return 0


def _cmd_simulate(args: argparse.Namespace) -> int:
    """Replay a sequence of synthetic events through the engine."""
    import time
    from datetime import UTC, datetime

    from ..config.models import Config, RuntimeConfig
    from ..core.decisions import EnforcementMode as DecisionMode
    from ..engine.facade import ActivityEngine
    from ..adapters.mock.action_executor import MockActionExecutor

    config = Config(runtime=RuntimeConfig(mode=DecisionMode(args.mode)))
    engine = ActivityEngine(config=config, executor=MockActionExecutor(), student_id="student-demo")
    session_id = engine.start_session()

    domains = [
        "classroom.google.com",
        "youtube.com",
        "docs.google.com",
        "facebook.com",
        "wikipedia.org",
    ]
    apps = ["Visual Studio Code", "Discord", "Chrome", "word"]

    async def _run() -> None:
        for i in range(args.events):
            source = i % 3
            if source == 0:
                raw = {
                    "kind": "browser_navigation",
                    "browser": {"domain": domains[i % len(domains)], "tab_id": f"tab-{i}"},
                }
            elif source == 1:
                raw = {
                    "kind": "process_focus",
                    "application": {"name": apps[i % len(apps)], "process": apps[i % len(apps)].lower()},
                }
            else:
                raw = {
                    "kind": "dns_request",
                    "network": {"domain": domains[i % len(domains)]},
                }
            await engine.feed_raw(raw)
            time.sleep(0.05)

        print(f"Simulated {args.events} events (mode={args.mode})")
        state = engine.current_state()
        if state:
            print(f"Final state: {state.state.value}")
            print(f"Risk score: {state.risk_score:.2f}")
        print("Metrics:", engine.metrics())

    asyncio.run(_run())
    engine.end_session()
    return 0


def _cmd_policy_check(args: argparse.Namespace) -> int:
    """Validate a policy YAML file."""
    from pathlib import Path

    from ..core.errors import ConfigurationError
    from ..policy.loader import PolicyLoader

    path = Path(args.path)
    try:
        policy = PolicyLoader(path).load()
    except ConfigurationError as exc:
        print(f"Policy check FAILED: {exc}")
        return 1

    print(f"Policy check PASSED for {path}")
    print(f"  Version : {policy.version}")
    print(f"  Focus   : enabled={policy.focus.enabled}")
    print(f"  Bedtime : enabled={policy.bedtime.enabled} start={policy.bedtime.start_time}")
    print(
        f"  Escalation: L1={policy.escalation.level_1_delay_seconds}s "
        f"L2={policy.escalation.level_2_delay_seconds}s "
        f"threshold={policy.escalation.level_3_violation_threshold}"
    )
    return 0