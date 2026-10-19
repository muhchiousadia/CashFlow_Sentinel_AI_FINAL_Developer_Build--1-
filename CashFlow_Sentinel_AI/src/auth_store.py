"""Local prototype authentication and persistent SQLite audit trail.
For internet-facing deployment use an identity provider, TLS, secret management and reviewed DB controls.
"""
from __future__ import annotations
import hashlib, hmac, os, secrets, sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_configured_db_path = Path(
    os.getenv('CFS_DB_PATH') or str(PROJECT_ROOT / 'data' / 'cfs_security.sqlite3')
).expanduser()
DB_PATH = (_configured_db_path if _configured_db_path.is_absolute() else PROJECT_ROOT / _configured_db_path).resolve()
ROLES = {'viewer', 'analyst', 'owner'}
ITERATIONS = 310_000
PASSWORD_SCHEME = 'pbkdf2_sha256_310000'

@contextmanager
def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    try:
        con.execute('PRAGMA journal_mode=WAL')
        con.execute('PRAGMA foreign_keys=ON')
        with con:
            yield con
    finally:
        con.close()

def init_db():
    with _connect() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY, full_name TEXT NOT NULL DEFAULT '',
            salt BLOB NOT NULL, password_hash BLOB NOT NULL,
            password_scheme TEXT NOT NULL DEFAULT 'unsupported',
            role TEXT NOT NULL CHECK(role IN ('viewer','analyst','owner')),
            created_utc TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1)''')
        user_columns = {row['name'] for row in con.execute('PRAGMA table_info(users)')}
        if 'full_name' not in user_columns:
            con.execute("ALTER TABLE users ADD COLUMN full_name TEXT NOT NULL DEFAULT ''")
        if 'password_scheme' not in user_columns:
            con.execute("ALTER TABLE users ADD COLUMN password_scheme TEXT NOT NULL DEFAULT 'unsupported'")
            con.execute(
                '''UPDATE users SET password_scheme=?
                   WHERE length(salt)=16 AND length(password_hash)=32''',
                (PASSWORD_SCHEME,),
            )
        con.execute('''CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp_utc TEXT NOT NULL,
            username TEXT NOT NULL, role TEXT NOT NULL, event TEXT NOT NULL,
            resource TEXT NOT NULL, decision TEXT NOT NULL, details TEXT NOT NULL,
            external_action_executed INTEGER NOT NULL DEFAULT 0)''')
        con.execute('CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_log(timestamp_utc)')

def user_count():
    init_db()
    with _connect() as con: return int(con.execute('SELECT COUNT(*) FROM users WHERE active=1').fetchone()[0])

def _password_record(password: str, salt: bytes | None = None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, ITERATIONS)
    return salt, digest

def create_user(username: str, password: str, role: str, full_name: str | None = None):
    init_db()
    username = username.strip().lower()
    full_name = (full_name if full_name is not None else username).strip()
    if len(username) < 3 or len(username) > 64 or not username.replace('_','').replace('-','').isalnum():
        raise ValueError('Username must be 3–64 characters using letters, numbers, _ or -.')
    if not full_name or len(full_name) > 120:
        raise ValueError('Full name must be between 1 and 120 characters.')
    if len(password) < 12:
        raise ValueError('Password must be at least 12 characters.')
    if role not in ROLES: raise ValueError('Unsupported role.')
    salt, digest = _password_record(password)
    try:
        with _connect() as con:
            con.execute('''INSERT INTO users(
                username,full_name,salt,password_hash,password_scheme,role,created_utc
            ) VALUES(?,?,?,?,?,?,?)''',
                        (username, full_name, salt, digest, PASSWORD_SCHEME, role, datetime.now(timezone.utc).isoformat()))
    except sqlite3.IntegrityError as e:
        with _connect() as con:
            existing = con.execute(
                'SELECT 1 FROM users WHERE username=?',
                (username,),
            ).fetchone()
        if existing:
            raise ValueError('Username already exists.') from e
        raise
    return username

def authenticate(username: str, password: str):
    init_db(); username = username.strip().lower()
    with _connect() as con: row = con.execute('SELECT * FROM users WHERE username=? AND active=1', (username,)).fetchone()
    if not row:
        # Reduce username-enumeration timing differences.
        _password_record(password or '', b'\0' * 16)
        return None
    if row['password_scheme'] != PASSWORD_SCHEME or len(row['salt']) != 16 or len(row['password_hash']) != 32:
        _password_record(password or '', b'\0' * 16)
        return None
    _, digest = _password_record(password, row['salt'])
    if not hmac.compare_digest(digest, row['password_hash']): return None
    return {
        'username': row['username'],
        'full_name': row['full_name'] or row['username'],
        'role': row['role'],
    }

def write_audit(username: str, role: str, event: str, resource: str, decision: str, details: str = ''):
    init_db()
    if role not in ROLES: raise ValueError('Invalid audit role.')
    safe_details = ' '.join(str(details).split())[:1000]
    with _connect() as con:
        cur = con.execute('''INSERT INTO audit_log(timestamp_utc,username,role,event,resource,decision,details,external_action_executed)
        VALUES(?,?,?,?,?,?,?,0)''', (datetime.now(timezone.utc).isoformat(), username, role, str(event)[:80], str(resource)[:160], str(decision)[:40], safe_details))
        return int(cur.lastrowid)

def read_audit(limit: int = 500):
    init_db()
    with _connect() as con:
        rows = con.execute('SELECT id,timestamp_utc,username,role,event,resource,decision,details,external_action_executed FROM audit_log ORDER BY id DESC LIMIT ?', (max(1,min(int(limit),5000)),)).fetchall()
    return [dict(r) for r in rows]
