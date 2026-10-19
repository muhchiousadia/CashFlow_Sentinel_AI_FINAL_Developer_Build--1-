import pytest
from src.security_policy import authorize, AuthorizationError, make_audit_record, sanitize_note

def test_viewer_cannot_review():
    with pytest.raises(AuthorizationError):
        authorize("viewer", "review")

def test_analyst_cannot_review():
    with pytest.raises(AuthorizationError):
        authorize("analyst", "review")

def test_owner_can_review_and_no_external_action():
    record = make_audit_record("owner", "Test action", "Approved for human follow-up", "checked")
    assert record["external_action_executed"] is False
    assert record["decision"] == "Approved for human follow-up"

def test_unknown_role_blocked():
    with pytest.raises(AuthorizationError):
        authorize("superuser", "review")

def test_note_control_chars_removed_and_length_limited():
    assert sanitize_note("hello\x00world") == "helloworld"
    assert len(sanitize_note("x"*300)) == 250
