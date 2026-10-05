# Retention policy

STORED: Explicit string preferences, scoped by user ID, with at most 10 entries per user.

WHY: To preserve user-specific preferences without allowing one user's memory to answer another's.

CORRECTED BY: The user can overwrite a preference or reset all stored values for that user.

EXPIRES: Values remain until overwritten or reset; the per-user cap is 10 entries.

WE REFUSE TO REMEMBER: API keys, credentials, and other secrets.

## How the code enforces it

`MemoryStore` in `agent.py` scopes values by user ID, enforces its configured
per-user cap, and exposes `reset()`. The
`test_memory_is_capped_reset_and_kept_per_user` test verifies user isolation,
oldest-entry eviction at the cap, missing-key behavior, and per-user reset.
