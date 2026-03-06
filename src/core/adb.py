"""ADB client abstraction and helpers."""

import subprocess
import sys
from typing import List, Optional, Tuple

from .config import (
    get_adb_executable,
    ADB_DEVICES_TIMEOUT,
    ADB_SHELL_TIMEOUT,
    ADB_PULL_PUSH_TIMEOUT,
)


class AdbClient:
    """Object-oriented wrapper around the adb executable."""

    def __init__(self, executable: Optional[str] = None) -> None:
        self._executable = executable or get_adb_executable()

    def _run(
        self,
        args: List[str],
        timeout: int = ADB_DEVICES_TIMEOUT,
        capture: bool = True,
    ) -> Tuple[int, str, str]:
        """Run an adb command and return (returncode, stdout, stderr)."""
        cmd = [self._executable] + args
        kwargs = dict(
            capture_output=capture,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        try:
            result = subprocess.run(cmd, **kwargs)
            out = (result.stdout or "").strip()
            err = (result.stderr or "").strip()
            return result.returncode, out, err
        except FileNotFoundError:
            return -1, "", f"adb not found: {self._executable}"
        except subprocess.TimeoutExpired:
            return -1, "", "command timed out"
        except Exception as exc:
            return -1, "", str(exc)

    def list_devices(self) -> List[Tuple[str, str]]:
        """Return list of connected devices as (serial, status)."""
        code, out, _ = self._run(["devices"], timeout=ADB_DEVICES_TIMEOUT)
        if code != 0:
            return []
        lines = [
            line.strip()
            for line in out.splitlines()
            if line.strip() and not line.startswith("List")
        ]
        devices: List[Tuple[str, str]] = []
        for line in lines:
            parts = line.split(None, 1)
            if len(parts) >= 2 and parts[1] == "device":
                devices.append((parts[0], parts[1]))
        return devices

    def shell(
        self,
        serial: str,
        command: str,
        timeout: int = ADB_SHELL_TIMEOUT,
    ) -> Tuple[int, str, str]:
        """Execute a shell command on the given device."""
        return self._run(["-s", serial, "shell", command], timeout=timeout)

    def pull(
        self,
        serial: str,
        remote_path: str,
        local_path: str,
        timeout: int = ADB_PULL_PUSH_TIMEOUT,
    ) -> Tuple[bool, str]:
        """Pull a file or directory from device to host."""
        code, out, err = self._run(
            ["-s", serial, "pull", remote_path, local_path],
            timeout=timeout,
        )
        if code == 0:
            return True, out or "Download finished."
        return False, err or out or f"pull failed (code {code})"

    def push(
        self,
        serial: str,
        local_path: str,
        remote_path: str,
        timeout: int = ADB_PULL_PUSH_TIMEOUT,
    ) -> Tuple[bool, str]:
        """Push a file or directory from host to device."""
        code, out, err = self._run(
            ["-s", serial, "push", local_path, remote_path],
            timeout=timeout,
        )
        if code == 0:
            return True, out or "Upload finished."
        return False, err or out or f"push failed (code {code})"


# Backwards-compatible module-level helpers using a shared client.
_DEFAULT_CLIENT = AdbClient()


def get_devices() -> List[Tuple[str, str]]:
    return _DEFAULT_CLIENT.list_devices()


def shell(serial: str, command: str, timeout: int = ADB_SHELL_TIMEOUT) -> Tuple[int, str, str]:
    return _DEFAULT_CLIENT.shell(serial, command, timeout=timeout)


def pull(serial: str, remote_path: str, local_path: str, timeout: int = ADB_PULL_PUSH_TIMEOUT) -> Tuple[bool, str]:
    return _DEFAULT_CLIENT.pull(serial, remote_path, local_path, timeout=timeout)


def push(serial: str, local_path: str, remote_path: str, timeout: int = ADB_PULL_PUSH_TIMEOUT) -> Tuple[bool, str]:
    return _DEFAULT_CLIENT.push(serial, local_path, remote_path, timeout=timeout)


def sync_time_to_rtc(serial: str, time_str: str) -> Tuple[bool, str]:
    """Set system time on device and write it to hardware RTC."""
    cmd = f"date -s '{time_str}' && hwclock -w"
    code, out, err = shell(serial, cmd, timeout=ADB_SHELL_TIMEOUT)
    if code == 0:
        return True, ("Time synchronized and written to RTC." + (out or ""))
    msg = err or out or f"exit code {code}"
    return False, f"Time sync failed: {msg}"
