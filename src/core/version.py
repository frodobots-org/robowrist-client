"""Read device version from /userdata/version.json."""

import json
from typing import Optional, Dict, Any

from . import adb
from .config import ADB_SHELL_TIMEOUT


def get_device_version(serial: str, timeout: int = ADB_SHELL_TIMEOUT) -> Optional[Dict[str, Any]]:
    """
    Run `cat /userdata/version.json` on device and parse JSON.
    Returns dict with keys hardware_version, pcb_version, or None on failure.
    """
    code, out, _ = adb.shell(serial, "cat /userdata/version.json", timeout=timeout)
    if code != 0 or not out.strip():
        return None
    try:
        data = json.loads(out)
        return {
            "hardware_version": data.get("hardware_version", ""),
            "pcb_version": data.get("pcb_version", ""),
        }
    except (json.JSONDecodeError, TypeError):
        return None
