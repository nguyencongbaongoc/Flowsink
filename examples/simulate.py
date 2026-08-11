"""Example: simulate events through the Activity Engine."""

import asyncio

from activity_engine.config.models import Config, RuntimeConfig
from activity_engine.core.decisions import EnforcementMode
from activity_engine.engine.facade import ActivityEngine
from activity_engine.adapters.mock.action_executor import MockActionExecutor

async def main() -> None:
    # 1. Create a facade with a mock action executor (safe default)
    config = Config(runtime=RuntimeConfig(mode=EnforcementMode.DRY_RUN))
    executor = MockActionExecutor()
    engine = ActivityEngine(config=config, executor=executor, student_id="ST001")

    # 2. Start a monitoring session
    session_id = engine.start_session()
    print(f"Session started: {session_id}")

    # 3. Simulate allowed and blocked events
    allowed = {
        "kind": "browser_navigation",
        "browser": {"domain": "classroom.google.com", "tab_id": "tab-1"},
    }
    blocked = {
        "kind": "browser_navigation",
        "browser": {"domain": "youtube.com", "tab_id": "tab-1"},
    }

    print("\nProcessing allowed event...")
    await engine.feed_raw(allowed)
    state = engine.current_state()
    print(f"State: {state.state.value if state else 'None'}")

    print("\nProcessing blocked event...")
    await engine.feed_raw(blocked)
    state = engine.current_state()
    print(f"State: {state.state.value if state else 'None'}")

    # 4. Show metrics
    print("\nMetrics:")
    for k, v in engine.metrics().items():
        print(f"  {k}: {v}")

    # 5. End session
    engine.end_session()
    print("\nSession ended.")

if __name__ == "__main__":
    asyncio.run(main())