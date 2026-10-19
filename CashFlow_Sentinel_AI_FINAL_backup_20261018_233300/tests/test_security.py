import pytest
from src.security import require_permission, AuthorizationError, make_audit_record


def test_viewer_can_view_but_cannot_run_or_review():
    require_permission("Tier 0 — Viewer", "view_forecast")
    with pytest.raises(AuthorizationError):
        require_permission("Tier 0 — Viewer", "run_simulation")
    with pytest.raises(AuthorizationError):
        make_audit_record("Tier 0 — Viewer", "Delay supplier payment", "Rejected", "x", "2026-10-15T00:00:00Z")


def test_analyst_can_simulate_but_cannot_record_owner_review():
    require_permission("Tier 1 — Analyst", "run_simulation")
    require_permission("Tier 1 — Analyst", "export_simulated_log")
    with pytest.raises(AuthorizationError):
        require_permission("Tier 1 — Analyst", "record_review")


def test_owner_review_record_is_sanitized_and_never_executes_action():
    record = make_audit_record("Tier 2 — Owner review", "A"*200, "Approved for human follow-up", "  evidence\n reviewed  ", "2026-10-15T00:00:00Z")
    assert record["role_demo"] == "Tier 2"
    assert len(record["action"]) == 120
    assert record["note"] == "evidence reviewed"
    assert record["external_action_executed"] is False


def test_invalid_decision_rejected():
    with pytest.raises(ValueError, match="Invalid review decision"):
        make_audit_record("Tier 2", "Action", "Execute now", "", "2026-10-15T00:00:00Z")


def test_all_roles_can_open_read_only_finance_chat():
    # Finance chat only reads selected transaction/forecast data.
    require_permission("Tier 0 — Viewer", "view_agent")
    require_permission("Tier 1 — Analyst", "view_agent")
    require_permission("Tier 2 — Owner review", "view_agent")
