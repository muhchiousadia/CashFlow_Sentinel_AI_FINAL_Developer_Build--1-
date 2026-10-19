"""Centralized demo permission policy.

This is testable application-level authorization for a local demonstration.
It is not identity authentication and must not be represented as production RBAC.
"""
from __future__ import annotations

ROLE_PERMISSIONS = {
    "Tier 0": frozenset({"view_forecast", "view_agent", "view_network_risk"}),
    "Tier 1": frozenset({"view_forecast", "view_agent", "view_network_risk", "run_simulation", "export_simulated_log"}),
    "Tier 2": frozenset({"view_forecast", "view_agent", "view_network_risk", "run_simulation", "export_simulated_log", "record_review"}),
}

class AuthorizationError(PermissionError):
    """Raised when the selected demo tier is not permitted to perform an action."""


def require_permission(role: str, action: str) -> None:
    role_key = str(role).split(" — ", 1)[0].strip()
    if role_key not in ROLE_PERMISSIONS:
        raise AuthorizationError(f"Unknown permission tier: {role_key}")
    if action not in ROLE_PERMISSIONS[role_key]:
        raise AuthorizationError(f"Permission denied: {role_key} cannot perform {action}")


def make_audit_record(role: str, action: str, decision: str, note: str,
                      timestamp_utc: str) -> dict:
    require_permission(role, "record_review")
    allowed_decisions = {"Needs more evidence", "Approved for human follow-up", "Rejected"}
    if decision not in allowed_decisions:
        raise ValueError("Invalid review decision")
    clean_note = " ".join(str(note).split())[:250]
    return {
        "timestamp_utc": str(timestamp_utc),
        "role_demo": str(role).split(" — ", 1)[0].strip(),
        "action": str(action)[:120],
        "decision": decision,
        "note": clean_note,
        "external_action_executed": False,
    }
