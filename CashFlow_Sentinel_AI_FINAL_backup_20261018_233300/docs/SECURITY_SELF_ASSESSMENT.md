# Security Self-Assessment — v0.8

## Implemented in this prototype
- Local username/password authentication backed by SQLite.
- Passwords are not stored in plaintext; PBKDF2-HMAC-SHA256 with per-user random salt and 310,000 iterations is used.
- Roles (`viewer`, `analyst`, `owner`) are stored with the account, not selected from a UI role dropdown.
- App review and login events are persisted in a SQLite audit table with UTC timestamps and `external_action_executed=0`.
- Input CSV schema/type validation and bounded notes.
- Financial actions are recommendations/simulations only; no bank or lending provider is integrated.

## Not implemented / not certified
- This is local-demo authentication, not production-grade IAM. No MFA, account recovery, lockout/rate limiting, session expiry policy, central identity provider, TLS termination, or secrets vault.
- SQLite audit storage is persistent on the same machine but not tamper-proof. No remote immutable log sink, backup policy, retention policy, or cryptographic chaining.
- No independent penetration test, privacy review, threat-model sign-off, or compliance certification has been completed.
- Do not expose this app to the public internet or use highly sensitive financial/customer data without additional controls and a security review.

## Manual acceptance tests
1. First launch asks to create an owner with a 12+ character password.
2. Correct credentials permit login; incorrect credentials are rejected.
3. The user cannot choose their own role in the dashboard; role comes from the account record.
4. Viewer cannot simulate or record owner review; analyst cannot record owner review; owner can record a review.
5. Restart app and confirm prior audit entries still appear for owner.
6. Confirm audit rows always show `external_action_executed=0`.
