# Architecture Guide

This module is built using Clean Architecture combined with Hexagonal Architecture (Ports & Adapters).

```mermaid
graph TD
    %% Telemetry input
    adapters_in[Windows Adapters / Extension / DNS] -->|Raw telemetry dicts| facade[ActivityEngine Facade]

    %% Inside Core / Facade
    facade --> event_engine[Event Engine]
    event_engine -->|Normalized ActivityEvents| policy_engine[Policy Engine]
    policy_engine -->|PolicyDecision| state_engine[State Engine]
    state_engine -->|StateSnapshot / Transitions| escalation_engine[Escalation Engine]
    escalation_engine -->|Idempotent ActionRequests| action_engine[Action Engine]

    %% Output execution
    action_engine -->|Typed payloads| adapters_out[Mock / Windows Action Executors]
```

## Packages

- **`core/`**: Platform-independent business logic (events, policies, state machine, errors).
- **`domain/`**: Aggregates and entities (monitoring sessions, current activity aggregate, violations).
- **`engine/`**: Pipeline processing nodes.
- **`ports/`**: Protocol/interfaces for monitors and executors.
- **`adapters/`**: Real and mock implementations of ports.
- **`services/`**: Coordination of multiple engines (Focus, Bedtime, Polling).
- **`transport/`**: Wire serialization contracts for websocket streams.