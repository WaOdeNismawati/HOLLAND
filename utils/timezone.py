from datetime import datetime
import pytz
from config import LOCAL_TIMEZONE

def convert_utc_to_local(utc_dt_str):
    """
    Konversi string datetime UTC ke datetime lokal yang diformat,
    berdasarkan zona waktu di config.py.
    """
    if not utc_dt_str:
        return None

    try:
        # Konversi string ke objek datetime
        utc_dt = datetime.strptime(utc_dt_str, '%Y-%m-%d %H:%M:%S')

        # Atur timezone ke UTC
        utc_tz = pytz.timezone('UTC')
        utc_dt = utc_tz.localize(utc_dt)

        # Konversi ke timezone lokal dari config
        local_tz = pytz.timezone(LOCAL_TIMEZONE)
        local_dt = utc_dt.astimezone(local_tz)

        # Format ke string yang mudah dibaca
        return local_dt.strftime('%d %B %Y, %H:%M')
    except pytz.UnknownTimeZoneError:
        return "Invalid Timezone in config.py"
    except ValueError:
        return "Invalid Datetime Format"