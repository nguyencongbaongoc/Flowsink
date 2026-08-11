# Policy Engine Syntax

Policies are defined in YAML files with this structure:

```yaml
version: "1"  # Schema version

focus:
  enabled: true
  allowed_domains:
    - classroom.google.com
    - docs.google.com
    - "*.google.com"  # Wildcards must be quoted
  blocked_domains:
    - facebook.com
    - tiktok.com
  allowed_apps:
    - Chrome
    - Visual Studio Code
  blocked_apps:
    - Discord
    - Steam
  allowed_url_patterns: []  # Future extension

escalation:
  level_1_delay_seconds: 10
  level_2_delay_seconds: 30
  level_3_violation_threshold: 3

bedtime:
  enabled: false
  start_time: "22:30"
  level_1_warning_minutes: 15
  level_2_warning_minutes: 5
  level_3_action: restricted_mode  # restricted_mode / shutdown / lock
```

## Validation

- `start_time` must be in `HH:MM` 24-hour format.
- Wildcard domains must be quoted (`"*.google.com"`) to avoid YAML alias parsing errors.
- All lists must contain strings only.

## Loading

```python
from activity_engine.policy.loader import PolicyLoader

policy = PolicyLoader("path/to/policy.yaml").load()
```

## Default Policy

A default policy is bundled in `src/activity_engine/policy/default_policies.yaml`. It can be loaded via:

```python
from activity_engine.policy.loader import load_default_policy

policy = load_default_policy()
```

## Escalation Flow

1. **Level 1**: Warning message shown to student.
2. **Level 2**: Browser redirected to allowed site or app closed.
3. **Level 3**: Device enters restricted mode (blocks all non-allowed domains/apps).

The escalation engine tracks violation counts per student/device pair and escalates based on `level_3_violation_threshold`.