from __future__ import annotations
from datetime import datetime, timezone
import re

class AuthorizationError(PermissionError):
    pass

ROLE_PERMISSIONS = {
    "viewer": {"view"},
    "analyst": {"view", "simulate", "export"},
    "owner": {"view", "simulate", "export", "review"},
}

def authorize(role: str, permission: str) -> bool:
    role = str(role).strip().lower()
    if role not in ROLE_PERMISSIONS:
        raise AuthorizationError("Unknown role.")
    if permission not in ROLE_PERMISSIONS[role]:
        raise AuthorizationError(f"Role '{role}' is not authorized for '{permission}'.")
    return True

def sanitize_note(note: str, max_length: int = 250) -> str:
    # Remove control characters; preserve ordinary punctuation and letters.
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", str(note))
    return cleaned.strip()[:max_length]

def make_audit_record(role: str, action: str, decision: str, note: str) -> dict:
    authorize(role, "review")
    allowed = {"Needs more evidence", "Approved for human follow-up", "Rejected"}
    if decision not in allowed:
        raise ValueError("Unsupported review decision.")
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "role": role,
        "action": str(action)[:120],
        "decision": decision,
        "note": sanitize_note(note),
        "external_action_executed": False,
    }
