from datetime import datetime

import pytz
import streamlit as st


DEFAULT_TIMEZONE = 'Asia/Makassar'


def _get_session_timezone():
    if not hasattr(st, "session_state"):
        return DEFAULT_TIMEZONE
    return getattr(st.session_state, 'timezone', DEFAULT_TIMEZONE)


def convert_utc_to_local(utc_dt_str):
    """Konversi string UTC standar ke waktu lokal pengguna."""
    if not utc_dt_str:
        return None

    try:
        utc_dt = datetime.strptime(utc_dt_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return "Format tanggal tidak valid"

    utc_dt = pytz.utc.localize(utc_dt)
    local_tz_str = _get_session_timezone()

    try:
        local_tz = pytz.timezone(local_tz_str)
    except pytz.UnknownTimeZoneError:
        local_tz = pytz.timezone(DEFAULT_TIMEZONE)

    local_dt = utc_dt.astimezone(local_tz)
    return local_dt.strftime('%d %B %Y, %H:%M')