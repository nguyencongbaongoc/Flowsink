# Security and Privacy Guide

This agent possesses administrative control over the student's device and must be treated as a security-sensitive component.

## Threat Model

### Privileges

- **Process Monitor**: Runs with standard user privileges on Windows (can enumerate processes and foreground window titles).
- **Action Executor**: Closing applications, blocking domains, and enabling restricted mode require Administrator privileges. If run as a standard user, these actions gracefully fail with `ADAPTER_ERROR` / `NOT_PERMITTED` without crashing the engine.

### Remote Execution Boundaries

The engine deliberately **exposes no shell execution APIs** or arbitrary command strings. Remote control is strictly limited to typed, schemas-validated actions:

- `WARN`
- `REDIRECT`
- `CLOSE_APPLICATION`
- `BLOCK_DOMAIN`
- `ENABLE_RESTRICTED_MODE`
- `DISABLE_RESTRICTED_MODE`

All action arguments are validated by Pydantic before routing to adapters.

## Privacy by Design

We adhere strictly to the principle of least privilege:

1. **No Keylogging**: Keystrokes are never monitored, captured, or transmitted.
2. **No Continuous Screen Capture**: Continuous recording, framing, or encoding of video is completely omitted.
3. **Selective Telemetry**: Browser events only include metadata (tab domain, URL, title) when explicitly permitted by policy. Form data, cookies, passwords, and private messages are never collected.
4. **Local Audit Logs**: Action execution results and policy decisions are stored locally in structured logs (`timestamp=... level=...`) to prevent leakage.