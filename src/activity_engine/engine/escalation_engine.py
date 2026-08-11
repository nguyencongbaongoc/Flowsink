"""Escalation Engine — orchestrates three-level enforcement.

Level 1 -> warning
Level 2 -> correction (redirect / close app / block domain)
Level 3 -> protected / restricted mode

The escalation engine only issues typed ActionRequests through the
ActionEngine. It never calls OS commands directly.
"""

from __future__ import annotations

from ..core.actions import (
    ActionRequest,
    ActionType,
    BlockDomainRequest,
    EnableRestrictedModeRequest,
    RedirectRequest,
    WarningRequest,
)
from ..core.decisions import PolicyDecision

class EscalationEngine:
    """Translates PolicyDecisions into a list of ActionRequests."""

    def __init__(self, default_policy_id: str = "focus-default") -> None:
        self._default_policy_id = default_policy_id

    def plan(self, decision: PolicyDecision) -> list[ActionRequest]:
        """Build the action plan for a decision."""
        student_id = decision.student_id or "unknown-student"
        actions: list[ActionRequest] = []

        for action_type in decision.action_types:
            if action_type not in (
                ActionType.WARN,
                ActionType.BLOCK_DOMAIN,
                ActionType.REDIRECT,
                ActionType.ENABLE_RESTRICTED_MODE,
            ):
                continue
            if action_type == ActionType.WARN:
                actions.append(
                    ActionRequest(
                        action=ActionType.WARN,
                        target=decision.domain or decision.application or "",
                        student_id=student_id,
                        policy_id=decision.policy_id,
                        reason=decision.reason,
                        payload=WarningRequest(
                            student_id=student_id,
                            policy_id=decision.policy_id,
                            reason=decision.reason,
                        ),
                    )
                )
            elif action_type == ActionType.BLOCK_DOMAIN and decision.domain:
                actions.append(
                    ActionRequest(
                        action=ActionType.BLOCK_DOMAIN,
                        target=decision.domain,
                        student_id=student_id,
                        policy_id=decision.policy_id,
                        reason=decision.reason,
                        payload=BlockDomainRequest(
                            student_id=student_id,
                            domain=decision.domain,
                            policy_id=decision.policy_id,
                            reason=decision.reason,
                        ),
                    )
                )
            elif action_type == ActionType.REDIRECT:
                actions.append(
                    ActionRequest(
                        action=ActionType.REDIRECT,
                        target=decision.domain or "",
                        student_id=student_id,
                        policy_id=decision.policy_id,
                        reason=decision.reason,
                        payload=RedirectRequest(
                            student_id=student_id,
                            target_domain=decision.domain or "",
                            policy_id=decision.policy_id,
                            reason=decision.reason,
                        ),
                    )
                )
            elif action_type == ActionType.ENABLE_RESTRICTED_MODE:
                actions.append(
                    ActionRequest(
                        action=ActionType.ENABLE_RESTRICTED_MODE,
                        target="device",
                        student_id=student_id,
                        policy_id=decision.policy_id,
                        reason=decision.reason,
                        payload=EnableRestrictedModeRequest(
                            student_id=student_id,
                            policy_id=decision.policy_id,
                            reason=decision.reason,
                        ),
                    )
                )
        return actions