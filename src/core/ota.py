"""OTA update: push package to /userdata/update_ota.tar and reboot recovery."""

from . import adb
from .config import ADB_PULL_PUSH_TIMEOUT

OTA_REMOTE_PATH = "/userdata/update_ota.tar"


def upload_ota(serial: str, local_path: str, timeout: int = ADB_PULL_PUSH_TIMEOUT) -> tuple:
    """
    Push local file to device as /userdata/update_ota.tar, then reboot recovery.
    Returns (success: bool, message: str).
    """
    ok, msg = adb.push(serial, local_path, OTA_REMOTE_PATH, timeout=timeout)
    if not ok:
        return False, msg
    code, out, err = adb.shell(serial, "sync && reboot recovery", timeout=30)
    if code != 0:
        return True, "OTA uploaded; reboot recovery may have failed: " + (err or out or str(code))
    return True, "OTA uploaded. Device is rebooting to recovery."
