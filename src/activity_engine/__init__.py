"""Student Activity Monitoring & Focus Control Engine.

Public API facade for the module. Only stable, cross-platform abstractions are
exported here. Consumers must never import ``activity_engine.adapters.*`` or
platform-specific internals.
"""

from .core.events import (
    ActivityEvent,
    ApplicationInfo,
    BrowserInfo,
    EventSource,
    EventType,
    NetworkInfo,
)
from .core.states import ActivityState, StateSnapshot
from .core.policies import (
    ActionMode,
    BedtimePolicy,
    EscalationPolicy,
    FocusPolicy,
    PolicyDocument,
)
from .core.actions import (
    ActionRequest,
    ActionStatus,
    ActionResult,
    ActionType,
    BlockDomainRequest,
    CloseApplicationRequest,
    EnableRestrictedModeRequest,
    RedirectRequest,
    WarningRequest,
)
from .core.decisions import EnforcementMode, PolicyDecision, PolicyOutcome
from .domain.session import MonitoringSession
from .engine import ActivityEngine

__version__ = "0.1.0"
API_VERSION = "v1"

__all__ = [
    "__version__",
    "API_VERSION",
    # Events
    "ActivityEvent",
    "ApplicationInfo",
    "BrowserInfo",
    "NetworkInfo",
    "EventSource",
    "EventType",
    # State
    "ActivityState",
    "StateSnapshot",
    # Policy
    "ActionMode",
    "BedtimePolicy",
    "EscalationPolicy",
    "FocusPolicy",
    "PolicyDocument",
    # Actions
    "ActionRequest",
    "ActionStatus",
    "ActionResult",
    "ActionType",
    "BlockDomainRequest",
    "CloseApplicationRequest",
    "EnableRestrictedModeRequest",
    "RedirectRequest",
    "WarningRequest",
    # Decisions
    "EnforcementMode",
    "PolicyDecision",
    "PolicyOutcome",
    # Facade
    "MonitoringSession",
    "ActivityEngine",
]