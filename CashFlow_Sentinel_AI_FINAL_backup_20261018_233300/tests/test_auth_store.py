import src.auth_store as auth
import sqlite3

def test_password_authentication_and_role(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, 'DB_PATH', tmp_path / 'test.sqlite3')
    auth.init_db()
    auth.create_user('owner_1', 'correct horse battery staple', 'owner')
    assert auth.authenticate('owner_1', 'correct horse battery staple')['role'] == 'owner'
    assert auth.authenticate('owner_1', 'wrong password') is None
    assert auth.authenticate('unknown', 'wrong password') is None

def test_password_policy_and_duplicate_user(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, 'DB_PATH', tmp_path / 'test.sqlite3')
    auth.create_user('owner_1', 'correct horse battery staple', 'owner')
    try: auth.create_user('weak', 'short', 'viewer')
    except ValueError as e: assert '12 characters' in str(e)
    else: assert False
    try: auth.create_user('owner_1', 'correct horse battery staple', 'owner')
    except ValueError as e: assert 'already exists' in str(e)
    else: assert False

def test_new_accounts_store_full_name_and_password_scheme(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, 'DB_PATH', tmp_path / 'test.sqlite3')
    auth.create_user('new_user', 'correct horse battery staple', 'viewer', 'Maya Chen')

    with sqlite3.connect(auth.DB_PATH) as con:
        full_name, salt, password_hash, scheme = con.execute(
            'SELECT full_name,salt,password_hash,password_scheme FROM users WHERE username=?',
            ('new_user',),
        ).fetchone()

    assert full_name == 'Maya Chen'
    assert len(salt) == 16
    assert len(password_hash) == 32
    assert password_hash != b'correct horse battery staple'
    assert scheme == auth.PASSWORD_SCHEME
    assert auth.authenticate('new_user', 'correct horse battery staple') == {
        'username': 'new_user',
        'full_name': 'Maya Chen',
        'role': 'viewer',
    }

def test_legacy_database_migration_preserves_users_and_rejects_unknown_hashes(tmp_path, monkeypatch):
    db_path = tmp_path / 'legacy.sqlite3'
    monkeypatch.setattr(auth, 'DB_PATH', db_path)
    salt, password_hash = auth._password_record('correct horse battery staple')
    with sqlite3.connect(db_path) as con:
        con.execute('''CREATE TABLE users (
            username TEXT PRIMARY KEY, salt BLOB NOT NULL, password_hash BLOB NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('viewer','analyst','owner')),
            created_utc TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1)''')
        con.execute(
            'INSERT INTO users(username,salt,password_hash,role,created_utc) VALUES(?,?,?,?,?)',
            ('legacy_user', salt, password_hash, 'viewer', '2026-01-01T00:00:00+00:00'),
        )
        con.execute(
            'INSERT INTO users(username,salt,password_hash,role,created_utc) VALUES(?,?,?,?,?)',
            ('unknown_hash', salt, b'unknown-hash-format', 'viewer', '2026-01-01T00:00:00+00:00'),
        )

    auth.init_db()

    assert auth.user_count() == 2
    assert auth.authenticate('legacy_user', 'correct horse battery staple')['role'] == 'viewer'
    assert auth.authenticate('unknown_hash', 'anything') is None
    with sqlite3.connect(db_path) as con:
        assert con.execute(
            'SELECT password_scheme FROM users WHERE username=?',
            ('unknown_hash',),
        ).fetchone()[0] == 'unsupported'

def test_database_constraint_errors_are_not_misreported_as_duplicate_users(tmp_path, monkeypatch):
    db_path = tmp_path / 'test.sqlite3'
    monkeypatch.setattr(auth, 'DB_PATH', db_path)
    auth.init_db()
    with sqlite3.connect(db_path) as con:
        con.execute('''CREATE TRIGGER reject_registration BEFORE INSERT ON users
            WHEN NEW.username='blocked_user'
            BEGIN SELECT RAISE(ABORT, 'registration blocked'); END''')

    try:
        auth.create_user('blocked_user', 'correct horse battery staple', 'viewer')
    except sqlite3.IntegrityError as exc:
        assert 'registration blocked' in str(exc)
    else:
        assert False

def test_database_connections_are_closed_after_auth_operations(tmp_path, monkeypatch):
    db_path = tmp_path / 'test.sqlite3'
    monkeypatch.setattr(auth, 'DB_PATH', db_path)
    auth.create_user('owner_1', 'correct horse battery staple', 'owner')
    assert auth.authenticate('owner_1', 'correct horse battery staple')
    db_path.unlink()
    assert not db_path.exists()

def test_audit_is_persistent_and_external_action_false(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, 'DB_PATH', tmp_path / 'test.sqlite3')
    auth.write_audit('owner_1', 'owner', 'HUMAN_REVIEW', 'supplier bill', 'Rejected', 'checked evidence')
    rows = auth.read_audit()
    assert len(rows) == 1
    assert rows[0]['decision'] == 'Rejected'
    assert rows[0]['external_action_executed'] == 0
