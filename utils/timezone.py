from datetime import datetime
import pytz

def convert_utc_to_local(utc_dt_str, local_tz_str='Asia/Jakarta'):
    """
    Konversi string datetime UTC ke datetime lokal yang diformat.
    """
    if not utc_dt_str:
        return None

    # Konversi string ke objek datetime
    utc_dt = datetime.strptime(utc_dt_str, '%Y-%m-%d %H:%M:%S')

    # Atur timezone ke UTC
    utc_tz = pytz.timezone('UTC')
    utc_dt = utc_tz.localize(utc_dt)

    # Konversi ke timezone lokal
    local_tz = pytz.timezone(local_tz_str)
    local_dt = utc_dt.astimezone(local_tz)

    # Format ke string yang mudah dibaca
    return local_dt.strftime('%d %B %Y, %H:%M')