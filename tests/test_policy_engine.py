"""Unit tests for the Policy Engine."""

from __future__ import annotations

import pytest

from activity_engine.core.actions import ActionType
from activity_engine.core.decisions import PolicyOutcome
from activity_engine.engine.policy_engine import PolicyEngine

class TestPolicyEngine:
    def test_allowed_domain(self, default_policy, make_browser_event):
        engine = PolicyEngine(default_policy, device_id="device-test", student_id="student-test")
        event = make_browser_event("classroom.google.com")
        decision = engine.evaluate(event)
        assert decision.outcome == PolicyOutcome.FOCUS
        assert decision.action_types == []

    def test_blocked_domain_warning(self, default_policy, make_browser_event):
        engine = PolicyEngine(default_policy, device_id="device-test", student_id="student-test")
        event = make_browser_event("youtube.com")
        decision = engine.evaluate(event)
        assert decision.outcome == PolicyOutcome.WARNING
        assert ActionType.WARN in decision.action_types
        assert engine.metrics["policy_violations"] == 1

    def test_allowed_app(self, default_policy, make_app_event):
        engine = PolicyEngine(default_policy, device_id="device-test", student_id="student-test")
        decision = engine.evaluate(make_app_event("Chrome"))
        assert decision.outcome == PolicyOutcome.ALLOWED
        assert decision.action_types == []

    def test_blocked_app(self, default_policy, make_app_event):
        engine = PolicyEngine(default_policy, device_id="device-test", student_id="student-test")
        decision = engine.evaluate(make_app_event("Discord"))
        assert decision.outcome == PolicyOutcome.WARNING
        assert ActionType.WARN in decision.action_types