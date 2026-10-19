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


def test_registration_login_and_logout_flow(tmp_path, monkeypatch):
    db_path = tmp_path / "app.sqlite3"
    monkeypatch.setattr(auth, "DB_PATH", db_path)
    at = AppTest.from_file(str(APP_PATH)).run()
    assert not at.exception

    _set_text(at, "owner_full_name", "Owner Test")
    _set_text(at, "login_username", "owner_test")
    _set_text(at, "login_password", "owner password 123")
    _set_text(at, "owner_confirm", "owner password 123")
    _click_button(at, "Create owner account")
    assert not at.exception
    assert "Create account" in [button.label for button in at.button]

    _click_button(at, "Create account")
    assert [field.key for field in at.text_input] == [
        "register_full_name",
        "register_username",
        "register_password",
        "register_confirm",
    ]
    assert "Show passwords" in [checkbox.label for checkbox in at.checkbox]
    at.checkbox(key="register_show_password").set_value(True).run()
    assert at.session_state["register_show_password"] is True
    at.checkbox(key="register_show_password").set_value(False).run()
    _click_button(at, "Create account")
    assert "Full name is required." in [message.value for message in at.error]

    _set_text(at, "register_full_name", "Maya Chen")
    _set_text(at, "register_username", "maya_chen")
    _set_text(at, "register_password", "a secure passphrase 123")
    _click_button(at, "Create account")
    assert "Password and confirmation are required." in [message.value for message in at.error]

    _set_text(at, "register_confirm", "a different passphrase 123")
    _click_button(at, "Create account")
    assert "Passwords do not match." in [message.value for message in at.error]

    _set_text(at, "register_confirm", "a secure passphrase 123")
    def fail_create_user(*args, **kwargs):
        raise sqlite3.OperationalError("simulated database failure")

    with monkeypatch.context() as patch:
        patch.setattr(auth, "create_user", fail_create_user)
        _click_button(at, "Create account")
        assert "The local account database could not save the account. Check database availability and try again." in [
            message.value for message in at.error
        ]

    _click_button(at, "Create account")
    assert "Account created. Sign in to continue." in [message.value for message in at.success]
    assert "register_password" not in at.session_state
    assert "register_confirm" not in at.session_state
    with sqlite3.connect(db_path) as con:
        full_name, password_hash = con.execute(
            "SELECT full_name,password_hash FROM users WHERE username=?",
            ("maya_chen",),
        ).fetchone()
    assert full_name == "Maya Chen"
    assert password_hash != b"a secure passphrase 123"

    _click_button(at, "Create account")
    _set_text(at, "register_full_name", "Another Maya")
    _set_text(at, "register_username", "maya_chen")
    _set_text(at, "register_password", "another secure passphrase")
    _set_text(at, "register_confirm", "another secure passphrase")
    _click_button(at, "Create account")
    assert "Username already exists." in [message.value for message in at.error]

    _click_button(at, "Already have an account? Sign in")
    _set_text(at, "login_username", "maya_chen")
    _set_text(at, "login_password", "not the correct passphrase")
    _click_button(at, "Sign in")
    assert "Invalid username or password." in [message.value for message in at.error]

    _set_text(at, "login_password", "a secure passphrase 123")
    _click_button(at, "Sign in")
    assert any("Signed in: maya_chen" in message.value for message in at.success)
    assert "login_password" not in at.session_state
    assert {
        "Cash-flow forecast",
        "Payment-delay stress test",
        "Explainable AI insights",
        "Explainable financial risk radar",
        "Illustrative financing comparison",
        "Supply-chain risk & counterparty vulnerability",
    }.issubset({heading.value for heading in at.subheader})
    assert not at.exception

    _click_button(at, "Sign out")
    assert "Sign in" in [button.label for button in at.button]
    assert not at.exception
