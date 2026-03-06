"""Network time retrieval and synchronization with device RTC."""

from datetime import datetime, timezone
from typing import Tuple

try:
    import ntplib
    HAS_NTP = True
except ImportError:
    HAS_NTP = False

from .config import DEFAULT_NTP_SERVERS, NTP_TIMEOUT
from . import adb as adb_module


class TimeSyncService:
    """Service that syncs host time to device RTC via adb."""

    def __init__(self) -> None:
        pass

    def get_network_time(self) -> Tuple[bool, datetime, str]:
        """Return (from_ntp, datetime, source_desc)."""
        if HAS_NTP:
            for server in DEFAULT_NTP_SERVERS:
                try:
                    client = ntplib.NTPClient()
                    resp = client.request(server, version=3, timeout=NTP_TIMEOUT)
                    dt_utc = datetime.utcfromtimestamp(resp.tx_time).replace(tzinfo=timezone.utc)
                    dt_local = dt_utc.astimezone().replace(tzinfo=None)
                    return True, dt_local, f"NTP ({server})"
                except Exception:
                    continue
        now = datetime.now()
        return False, now, "System time (NTP unavailable)"

    @staticmethod
    def format_time_for_device(dt: datetime) -> str:
        """Format datetime for device date -s: YYYY-MM-DD HH:MM:SS."""
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def sync_host_time_to_device(self, serial: str) -> Tuple[bool, str]:
        """Use host time to synchronize device RTC."""
        from_ntp, dt, source = self.get_network_time()
        time_str = self.format_time_for_device(dt)
        ok, msg = adb_module.sync_time_to_rtc(serial, time_str)
        prefix = "Time source: %s\n" % source
        if ok:
            return True, prefix + f"Synced time: {time_str}\n{msg}"
        return False, prefix + f"Pending time: {time_str}\n{msg}"
