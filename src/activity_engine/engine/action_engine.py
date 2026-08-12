"""Action Engine — executes typed enforcement actions through adapters.

Responsibilities:
- Route :class:`ActionRequest` objects to the configured ``ActionExecutor``.
- Enforce the runtime mode (dry_run / audit_only / enforce).
- Preserve idempotency (no repeated system mutations).
- Apply per-action timeout and error handling so a failing action never
  crashes the monitoring pipeline.
"""

from __future__ import annotations

import asyncio

from ..core.actions import (
    ActionRequest,
    ActionResult,
    ActionStatus,
    ActionType,
    BlockDomainRequest,
    CloseApplicationRequest,
    RedirectRequest,
    RestrictedModeRequest,
    WarningRequest,
)
from ..core.decisions import EnforcementMode
from ..logging import get_logger

_logger = get_logger("activity_engine.action_engine", component="ACTION", event="EXECUTE")

_DEFAULT_TIMEOUT_SECONDS = 10.0


class ActionEngine:
    """Safe executor facade over an ActionExecutor adapter."""

    def __init__(
        self,
        executor: object,
        mode: EnforcementMode = EnforcementMode.DRY_RUN,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._executor = executor
        self._mode = mode
        self._timeout_seconds = timeout_seconds
        self._completed: set[tuple[ActionType, str, str]] = set()
        self._restricted_mode_active = False
        self.metrics = {
            "actions_success": 0,
            "actions_failed": 0,
            "actions_skipped": 0,
            "actions_not_executed": 0,
        }

    async def execute(self, request: ActionRequest) -> ActionResult:
        """Execute a typed action, respecting mode and idempotency."""
        idempotency_key = (request.action, request.target, request.student_id)

        if self._mode == EnforcementMode.DRY_RUN:
            _logger.info(
                "action=%s target=%s reason=dry_run",
                request.action.value,
                request.target,
                event="NOT_EXECUTED",
                component="ACTION",
            )
            return self._not_executed(request, "dry_run")
        if self._mode == EnforcementMode.AUDIT_ONLY:
            _logger.info(
                "action=%s target=%s reason=audit_only",
                request.action.value,
                request.target,
                event="NOT_EXECUTED",
                component="ACTION",
            )
            return self._not_executed(request, "audit_only")

        if idempotency_key in self._completed:
            self.metrics["actions_skipped"] += 1
            return ActionResult(
                action_id=request.action_id,
                action=request.action,
                target=request.target,
                policy_id=request.policy_id,
                reason=request.reason,
                student_id=request.student_id,
                status=ActionStatus.SKIPPED,
                metadata={"note": "idempotent_duplicate"},
            )

        try:
            result = await self._dispatch(request)
        except asyncio.TimeoutError:
            self.metrics["actions_failed"] += 1
            return self._failed(request, "TIMEOUT", f"Action exceeded {self._timeout_seconds}s")
        except Exception as exc:  # noqa: BLE001 - adapter failures must not crash engine
            self.metrics["actions_failed"] += 1
            return self._failed(request, "ADAPTER_ERROR", str(exc))

        if result.status == ActionStatus.SUCCESS:
            self._completed.add(idempotency_key)
            self.metrics["actions_success"] += 1
            if request.action == ActionType.ENABLE_RESTRICTED_MODE:
                self._restricted_mode_active = True
            elif request.action == ActionType.DISABLE_RESTRICTED_MODE:
                self._restricted_mode_active = False
            _logger.info(
                "action=%s target=%s action_id=%s",
                request.action.value,
                request.target,
                request.action_id,
                event="SUCCESS",
                component="ACTION",
            )
        else:
            self.metrics["actions_failed"] += 1
            _logger.warning(
                "action=%s target=%s status=%s",
                request.action.value,
                request.target,
                result.status.value,
                event="FAILED",
                component="ACTION",
            )
        return result

    async def _dispatch(self, request: ActionRequest) -> ActionResult:
        """Route to the adapter method with a timeout."""
        executor = self._executor
        method = getattr(executor, request.action.value.lower(), None)
        if method is None:
            return self._failed(
                request,
                "UNSUPPORTED",
                f"Executor does not support {request.action.value}",
            )

        request_dict = self._to_adapter_payload(request)
        return await asyncio.wait_for(method(request_dict), timeout=self._timeout_seconds)

    def _not_executed(self, request: ActionRequest, reason: str) -> ActionResult:
        self.metrics["actions_not_executed"] += 1
        return ActionResult(
            action_id=request.action_id,
            action=request.action,
            target=request.target,
            policy_id=request.policy_id,
            reason=request.reason,
            student_id=request.student_id,
            status=ActionStatus.NOT_EXECUTED,
            metadata={"mode": str(self._mode.value), "reason": reason},
        )

    @staticmethod
    def _failed(request: ActionRequest, error_code: str, message: str) -> ActionResult:
        return ActionResult(
            action_id=request.action_id,
            action=request.action,
            target=request.target,
            policy_id=request.policy_id,
            reason=request.reason,
            student_id=request.student_id,
            status=ActionStatus.FAILED,
            error_code=error_code,
            error_message=message,
        )

    @staticmethod
    def _to_adapter_payload(request: ActionRequest) -> dict[str, object]:
        """Convert a typed request into the adapter-facing dict payload."""
        payload: dict[str, object] = {
            "action_id": request.action_id,
            "action": request.action.value,
            "target": request.target,
            "student_id": request.student_id,
            "policy_id": request.policy_id,
            "reason": request.reason,
        }
        if isinstance(request.payload, WarningRequest):
            payload["message"] = request.payload.message
        elif isinstance(request.payload, RedirectRequest):
            payload["allowed_url"] = request.payload.allowed_url
            payload["target_domain"] = request.payload.target_domain
        elif isinstance(request.payload, CloseApplicationRequest):
            payload["application"] = request.payload.application
            payload["process"] = request.payload.process
        elif isinstance(request.payload, BlockDomainRequest):
            payload["domain"] = request.payload.domain
        elif isinstance(request.payload, RestrictedModeRequest):
            payload["mode_name"] = request.payload.mode_name
        return payload

    def build_request(
        self,
        action: ActionType,
        target: str,
        student_id: str,
        policy_id: str = "focus-default",
        reason: str = "",
        payload: object | None = None,
    ) -> ActionRequest:
        """Build an ActionRequest for the given typed action."""
        return ActionRequest(
            action=action,
            target=target,
            student_id=student_id,
            policy_id=policy_id,
            reason=reason,
            payload=payload,  # type: ignore[arg-type]
        )