import sqlite3
from pathlib import Path

import src.auth_store as auth
from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def _click_button(at: AppTest, label: str) -> None:
    matches = [button for button in at.button if button.label == label]
    assert len(matches) == 1
    matches[0].click().run()


def _set_text(at: AppTest, key: str, value: str) -> None:
    at.text_input(key=key).set_value(value)


def test_registration_login_logout_and_dashboard_access(tmp_path, monkeypatch):
    db_path = tmp_path / "app.sqlite3"
    monkeypatch.setattr(auth, "DB_PATH", db_path)
    at = AppTest.from_file(str(APP_PATH)).run()
    assert not at.exception
    assert not at.subheader

    _set_text(at, "first_owner_full_name", "Owner Test")
    _set_text(at, "first_owner_username", "owner_test")
    _set_text(at, "first_owner_password", "owner password 123")
    _set_text(at, "first_owner_confirm", "owner password 123")
    _click_button(at, "Create owner account")
    assert not at.exception
    assert "Create account" in [button.label for button in at.button]
    assert "Don't have an account? Create one." in [caption.value for caption in at.caption]

    _click_button(at, "Create account")
    assert "Already have an account? Login." in [caption.value for caption in at.caption]
    assert "Login" in [button.label for button in at.button]
    assert at.text_input(key="register_password").proto.type == 1
    at.checkbox(key="register_show_password").set_value(True).run()
    assert at.text_input(key="register_password").proto.type == 0
    at.checkbox(key="register_show_password").set_value(False).run()
    _click_button(at, "Create account")
    assert "Full name, username, password, and confirmation are required." in [
        message.value for message in at.error
    ]

    _set_text(at, "register_full_name", "Maya Chen")
    _set_text(at, "register_username", "maya_chen")
    _set_text(at, "register_password", "a secure passphrase 123")
    _set_text(at, "register_confirm", "a different passphrase 123")
    _click_button(at, "Create account")
    assert "Passwords do not match." in [message.value for message in at.error]

    _set_text(at, "register_confirm", "a secure passphrase 123")
    with sqlite3.connect(db_path) as con:
        con.execute('''CREATE TRIGGER reject_viewer_registration BEFORE INSERT ON users
            WHEN NEW.username='maya_chen'
            BEGIN SELECT RAISE(ABORT, 'simulated database constraint'); END''')
    _click_button(at, "Create account")
    assert "The local account database could not save your account. Check database availability and try again." in [
        message.value for message in at.error
    ]
    with sqlite3.connect(db_path) as con:
        con.execute("DROP TRIGGER reject_viewer_registration")

    _click_button(at, "Create account")
    assert "Account created. Sign in with your new credentials." in [
        message.value for message in at.success
    ]
    assert not at.exception
    with sqlite3.connect(db_path) as con:
        full_name, password_hash, scheme = con.execute(
            "SELECT full_name,password_hash,password_scheme FROM users WHERE username=?",
            ("maya_chen",),
        ).fetchone()
        assert con.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 2
    assert full_name == "Maya Chen"
    assert password_hash != b"a secure passphrase 123"
    assert scheme == auth.PASSWORD_SCHEME

    _click_button(at, "Create account")
    _set_text(at, "register_full_name", "Another Maya")
    _set_text(at, "register_username", "maya_chen")
    _set_text(at, "register_password", "another secure passphrase")
    _set_text(at, "register_confirm", "another secure passphrase")
    _click_button(at, "Create account")
    assert "Username already exists." in [message.value for message in at.error]

    _click_button(at, "Login")
    assert at.text_input(key="login_password").proto.type == 1
    at.checkbox(key="login_show_password").set_value(True).run()
    assert at.text_input(key="login_password").proto.type == 0
    at.checkbox(key="login_show_password").set_value(False).run()
    _click_button(at, "Login")
    assert "Enter your username and password." in [message.value for message in at.error]
    _set_text(at, "login_username", "maya_chen")
    _set_text(at, "login_password", "incorrect secure passphrase")
    _click_button(at, "Login")
    assert "Invalid username or password." in [message.value for message in at.error]

    _set_text(at, "login_password", "a secure passphrase 123")
    _click_button(at, "Login")
    assert any("Signed in: maya_chen" in message.value for message in at.success)
    assert {
        "1. Baseline forecast",
        "2. Payment-delay shock test",
        "5. AI Agent — explainable decision brief",
        "9. Explainable Financial Risk Radar",
        "10. Smart Financing & Micro-Loan — mock comparison",
        "11. Supply Chain Cascade Risk & Counterparty Vulnerability Matrix",
    }.issubset({heading.value for heading in at.subheader})
    assert not at.exception

    _click_button(at, "Sign out")
    assert "Login" in [button.label for button in at.button]
    assert not at.subheader
    assert not at.exception
    auth.init_db()
    assert auth.authenticate("maya_chen", "a secure passphrase 123")
    restarted_app = AppTest.from_file(str(APP_PATH)).run()
    assert not restarted_app.exception
    assert "Create account" in [button.label for button in restarted_app.button]
