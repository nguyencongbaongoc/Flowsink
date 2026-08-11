"""Policy evaluation — turns events into PolicyDecision objects.

The evaluator is pure: no OS calls, no subprocess, no side effects. It only
classifies events against the active :class:`PolicyDocument` and returns
:class:`PolicyDecision` objects that the Action Engine may execute.
"""

from __future__ import annotations

from datetime import UTC, datetime

from ..core.actions import ActionType
from ..core.decisions import PolicyDecision, PolicyOutcome
from ..core.events import ActivityEvent, EventSource, EventType
from ..core.policies import EnforcementLevel, FocusPolicy, PolicyDocument
from .classifier import app_matches, domain_matches, normalize_domain

class PolicyEvaluator:
    """Evaluates single events against a policy document."""

    def __init__(self, policy: PolicyDocument) -> None:
        self._policy = policy

    @property
    def policy(self) -> PolicyDocument:
        return self._policy

    def set_policy(self, policy: PolicyDocument) -> None:
        self._policy = policy

    def evaluate(self, event: ActivityEvent) -> PolicyDecision:
        """Evaluate one event and return a decision."""
        if not self._policy.focus.enabled and not self._policy.bedtime.enabled:
            return self._decision(event, PolicyOutcome.IGNORED, reason="no_policy_enabled")

        # Network DNS events are never treated as certain violations on their own.
        if event.source == EventSource.NETWORK:
            return self._evaluate_network(event)

        domain = normalize_domain(event.browser.domain or event.browser.url or event.network.domain)
        app_name = event.application.name
        process = event.application.process
        focus = self._policy.focus

        if domain or event.browser.domain or event.browser.url or event.browser.tab_id:
            return self._evaluate_browser(event, domain, focus)
        if app_name or process:
            return self._evaluate_application(event, app_name, process, focus)

        return self._decision(event, PolicyOutcome.IGNORED, reason="no_actionable_target")

    def _evaluate_network(self, event: ActivityEvent) -> PolicyDecision:
        domain = normalize_domain(event.network.domain)
        focus = self._policy.focus
        if domain and focus.enabled:
            if domain_matches(domain, focus.allowed_domains):
                return self._decision(
                    event,
                    PolicyOutcome.FOCUS,
                    reason="dns_allowed_domain",
                    risk_score=0.0,
                    domain=domain,
                )
            if domain_matches(domain, focus.blocked_domains):
                # DNS traffic alone is corroborating evidence, not proof of active tab.
                return PolicyDecision(
                    event_id=event.event_id,
                    student_id=event.student_id,
                    outcome=PolicyOutcome.POTENTIAL_ACTIVITY,
                    targets=[domain],
                    domain=domain,
                    reason="dns_activity_possible_off_task_corroboration",
                    risk_score=0.4,
                )
        return self._decision(event, PolicyOutcome.IGNORED, reason="dns_no_policy_match")

    def _evaluate_browser(
        self,
        event: ActivityEvent,
        domain: str | None,
        focus: FocusPolicy,
    ) -> PolicyDecision:
        if domain:
            if domain_matches(domain, focus.allowed_domains):
                return self._decision(
                    event,
                    PolicyOutcome.FOCUS,
                    reason="browser_allowed_domain",
                    risk_score=0.0,
                    domain=domain,
                )
            if domain_matches(domain, focus.blocked_domains):
                return PolicyDecision(
                    event_id=event.event_id,
                    student_id=event.student_id,
                    outcome=PolicyOutcome.WARNING,
                    level=EnforcementLevel.LEVEL_1,
                    action_types=[ActionType.WARN],
                    targets=[domain],
                    domain=domain,
                    reason="browser_blocked_domain",
                    risk_score=0.7,
                )
            return self._decision(
                event,
                PolicyOutcome.ALLOWED,
                reason="browser_unlisted_domain",
                risk_score=0.1,
                domain=domain,
            )
        return self._decision(event, PolicyOutcome.ALLOWED, reason="browser_no_domain", risk_score=0.0)

    def _evaluate_application(
        self,
        event: ActivityEvent,
        app_name: str | None,
        process: str | None,
        focus: FocusPolicy,
    ) -> PolicyDecision:
        if app_matches(app_name, process, focus.blocked_apps):
            return PolicyDecision(
                event_id=event.event_id,
                student_id=event.student_id,
                outcome=PolicyOutcome.WARNING,
                level=EnforcementLevel.LEVEL_1,
                action_types=[ActionType.WARN],
                targets=[app_name or process or ""],
                application=app_name or process,
                reason="app_blocked",
                risk_score=0.7,
            )
        if app_matches(app_name, process, focus.allowed_apps):
            return self._decision(
                event,
                PolicyOutcome.ALLOWED,
                reason="app_allowed",
                risk_score=0.0,
                application=app_name or process,
            )
        return self._decision(
            event,
            PolicyOutcome.ALLOWED,
            reason="app_unlisted",
            risk_score=0.1,
            application=app_name or process,
        )

    def _decision(
        self,
        event: ActivityEvent,
        outcome: PolicyOutcome,
        reason: str,
        risk_score: float = 0.0,
        domain: str | None = None,
        application: str | None = None,
    ) -> PolicyDecision:
        return PolicyDecision(
            event_id=event.event_id,
            student_id=event.student_id,
            outcome=outcome,
            reason=reason,
            risk_score=risk_score,
            domain=domain,
            application=application,
        )

    def escalate(
        self,
        decision: PolicyDecision,
        violation_count: int,
        duration_seconds: float,
    ) -> PolicyDecision:
        """Escalate a WARNING decision based on duration and repeat count.

        Returns a new decision with a higher level and corresponding actions.
        """
        if decision.outcome != PolicyOutcome.WARNING:
            return decision

        esc = self._policy.escalation
        level1_delay = esc.level_1_delay_seconds
        level2_delay = esc.level_2_delay_seconds
        threshold = esc.level_3_violation_threshold

        level = EnforcementLevel.LEVEL_1
        actions = [ActionType.WARN]
        reason = decision.reason

        if duration_seconds >= level2_delay or violation_count >= 2:
            level = EnforcementLevel.LEVEL_2
            actions = [ActionType.WARN, ActionType.BLOCK_DOMAIN, ActionType.REDIRECT]
            reason = f"{decision.reason}_escalated_l2"
        if violation_count >= threshold or duration_seconds >= max(level2_delay * 2, 60):
            level = EnforcementLevel.LEVEL_3
            actions = [ActionType.WARN, ActionType.ENABLE_RESTRICTED_MODE]
            reason = f"{decision.reason}_escalated_l3"

        return decision.model_copy(
            update={
                "level": level,
                "action_types": actions,
                "reason": reason,
                "risk_score": min(1.0, decision.risk_score + 0.1 * (int(level.value[-1]) - 1)),
            }
        )

    def now_utc(self) -> datetime:
        return datetime.now(UTC)