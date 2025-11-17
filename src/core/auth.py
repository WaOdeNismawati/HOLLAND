from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

import bcrypt
import streamlit as st

from src.infrastructure.database.db_manager import DatabaseManager


SESSION_TIMEOUT = timedelta(days=1)  # Sesi akan kadaluarsa setelah 1 hari
SESSION_TIMEOUT_SECONDS = SESSION_TIMEOUT.total_seconds()
UTC = timezone.utc


@dataclass(frozen=True)
class SessionInfo:
    user_id: int
    username: str
    role: str
    full_name: str
    class_name: str | None = None


def authenticate_user(username, password):
    """Autentikasi user berdasarkan username dan password"""
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, username, password, role, full_name, class_name
        FROM users WHERE username = ?
    ''', (username,))
    
    user = cursor.fetchone()
    conn.close()
    
    if user and bcrypt.checkpw(password.encode('utf-8'), user[2]):
        return user
    return None

def hash_password(password):
    """Hash password menggunakan bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


def _redirect_to_login(message: str | None = None):
    if message:
        st.error(message)
    st.switch_page("app.py")
    st.stop()


def _normalize_timestamp(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, datetime):
        return value.timestamp()
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            try:
                return datetime.fromisoformat(value).timestamp()
            except ValueError:
                return None
    return None


def _session_expired(last_active_ts: float | None) -> bool:
    if not last_active_ts:
        return False
    return (time.time() - last_active_ts) > SESSION_TIMEOUT_SECONDS


def refresh_session_activity():
    st.session_state.last_active = time.time()


def check_login():
    """Cek apakah user sudah login dan sesi belum kadaluarsa"""
    logged_in = st.session_state.get('logged_in')
    last_active_ts = _normalize_timestamp(st.session_state.get('last_active'))

    if logged_in and st.session_state.get('last_active') != last_active_ts:
        st.session_state.last_active = last_active_ts

    if not logged_in:
        _redirect_to_login("Anda harus login terlebih dahulu!")
        return

    if _session_expired(last_active_ts):
        logout(message="Sesi berakhir, silakan login kembali.")
        return

    refresh_session_activity()


def require_role(allowed_roles: Iterable[str] | str):
    roles = {allowed_roles} if isinstance(allowed_roles, str) else set(allowed_roles)

    if 'logged_in' not in st.session_state:
        _redirect_to_login("Anda harus login terlebih dahulu!")

    check_login()

    user_role = st.session_state.get('role')
    if user_role not in roles:
        logout(message="Akses ditolak untuk peran Anda.")


def logout(*, message: str | None = None):
    """Logout user"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    if message:
        st.session_state['logout_message'] = message
    st.switch_page("app.py")
    st.stop()
