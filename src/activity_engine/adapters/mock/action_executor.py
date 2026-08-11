"""Mock action executor for tests and simulation."""

from __future__ import annotations

from typing import Any

from ...core.actions import ActionResult, ActionStatus, ActionType

class MockActionExecutor:
    """Configurable fake of the ActionExecutor port."""

    def __init__(self) -> None:
        self.executed: list[dict[str, Any]] = []
        self.mode = "enforce"

    async def warn(self, request: dict[str, Any]) -> dict[str, Any]:
        result = ActionResult(
            action_id=request["action_id"],
            action=ActionType.WARN,
            target=request.get("target", ""),
            policy_id=request.get("policy_id", "focus-default"),
            reason=request.get("reason", ""),
            student_id=request.get("student_id", ""),
            status=ActionStatus.SUCCESS,
        )
        self.executed.append(result.model_dump())
        return result.model_dump()

    async def redirect(self, request: dict[str, Any]) -> dict[str, Any]:
        result = ActionResult(
            action_id=request["action_id"],
            action=ActionType.REDIRECT,
            target=request.get("target", ""),
            policy_id=request.get("policy_id", "focus-default"),
            reason=request.get("reason", ""),
            student_id=request.get("student_id", ""),
            status=ActionStatus.SUCCESS,
        )
        self.executed.append(result.model_dump())
        return result.model_dump()

    async def close_application(self, request: dict[str, Any]) -> dict[str, Any]:
        result = ActionResult(
            action_id=request["action_id"],
            action=ActionType.CLOSE_APPLICATION,
            target=request.get("target", ""),
            policy_id=request.get("policy_id", "focus-default"),
            reason=request.get("reason", ""),
            student_id=request.get("student_id", ""),
            status=ActionStatus.SUCCESS,
        )
        self.executed.append(result.model_dump())
        return result.model_dump()

    async def block_domain(self, request: dict[str, Any]) -> dict[str, Any]:
        result = ActionResult(
            action_id=request["action_id"],
            action=ActionType.BLOCK_DOMAIN,
            target=request.get("target", ""),
            policy_id=request.get("policy_id", "focus-default"),
            reason=request.get("reason", ""),
            student_id=request.get("student_id", ""),
            status=ActionStatus.SUCCESS,
        )
        self.executed.append(result.model_dump())
        return result.model_dump()

    async def enable_restricted_mode(self, request: dict[str, Any]) -> dict[str, Any]:
        result = ActionResult(
            action_id=request["action_id"],
            action=ActionType.ENABLE_RESTRICTED_MODE,
            target=request.get("target", ""),
            policy_id=request.get("policy_id", "focus-default"),
            reason=request.get("reason", ""),
            student_id=request.get("student_id", ""),
            status=ActionStatus.SUCCESS,
        )
        self.executed.append(result.model_dump())
        return result.model_dump()

    async def disable_restricted_mode(self, request: dict[str, Any]) -> dict[str, Any]:
        result = ActionResult(
            action_id=request["action_id"],
            action=ActionType.DISABLE_RESTRICTED_MODE,
            target=request.get("target", ""),
            policy_id=request.get("policy_id", "focus-default"),
            reason=request.get("reason", ""),
            student_id=request.get("student_id", ""),
            status=ActionStatus.SUCCESS,
        )
        self.executed.append(result.model_dump())
        return result.model_dump()