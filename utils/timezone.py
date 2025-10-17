from datetime import datetime
import pytz
import streamlit as st

def convert_utc_to_local(utc_dt_str):
    """
    Konversi string datetime UTC ke datetime lokal yang diformat,
    berdasarkan zona waktu dari session state.
    """
    if not utc_dt_str:
        return None

    local_tz_str = st.session_state.get('timezone', 'Asia/Jakarta')

    try:
        # Konversi string ke objek datetime
        utc_dt = datetime.strptime(utc_dt_str, '%Y-%m-%d %H:%M:%S')

        # Atur timezone ke UTC
        utc_tz = pytz.timezone('UTC')
        utc_dt = utc_tz.localize(utc_dt)

        # Konversi ke timezone lokal dari session state
        local_tz = pytz.timezone(local_tz_str)
        local_dt = utc_dt.astimezone(local_tz)

        # Format ke string yang mudah dibaca
        return local_dt.strftime('%d %B %Y, %H:%M')
    except pytz.UnknownTimeZoneError:
        # Fallback jika timezone di session state tidak valid
        local_tz = pytz.timezone('Asia/Jakarta')
        local_dt = utc_dt.astimezone(local_tz)
        return local_dt.strftime('%d %B %Y, %H:%M')
    except ValueError:
        return "Invalid Datetime Format"