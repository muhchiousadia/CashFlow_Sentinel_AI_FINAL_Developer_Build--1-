# Security Test Matrix — v0.8

Automated tests: password hashing/authentication, wrong-password rejection, username uniqueness, role policy, owner-only review behavior, audit persistence, and `external_action_executed=0`. Run `python -m pytest -q`.

Manual checks: create first owner; sign in with correct and incorrect credentials; create viewer and analyst users as owner; verify role is account-bound; verify denied operations; restart the app and confirm audit entries persist.

Limitations: no MFA, lockout/rate limiting, recovery flow, TLS deployment, tamper-proof log sink, penetration test, or production security certification.
