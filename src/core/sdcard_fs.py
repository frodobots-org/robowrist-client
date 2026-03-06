import os
from typing import List, Tuple, Optional

from . import adb
from .config import ADB_SHELL_TIMEOUT, ADB_PULL_PUSH_TIMEOUT

ROOT = "/mnt/sdcard"


def _escape_path(path: str) -> str:
    """Escape single quotes for use inside single-quoted shell strings."""
    return path.replace("'", "'\\''")


def _norm_path(path: str) -> str:
    """Normalize path and ensure it stays under ROOT."""
    path = os.path.normpath(path).replace("\\", "/")
    if not path.startswith("/"):
        path = "/" + path
    if not path.startswith(ROOT):
        path = ROOT
    if path != ROOT and not path.startswith(ROOT + "/"):
        path = ROOT
    return path.rstrip("/") or ROOT


def _parse_ls_la(out: str) -> List[Tuple[str, bool, str, str]]:
    """Parse ls -la output into [(name, is_dir, size_str, mtime_str), ...]."""
    result = []
    for line in out.splitlines():
        line = line.strip()
        if not line or line.startswith("total "):
            continue
        parts = line.split()
        if len(parts) < 9:
            continue
        mode = parts[0]
        if len(mode) < 1 or mode[0] not in ("d", "-", "l", "s", "b", "c", "p"):
            continue
        is_dir = mode.startswith("d")
        try:
            size_str = parts[4]
            mtime_str = "%s %s %s" % (parts[5], parts[6], parts[7])
            name = " ".join(parts[8:]).strip()
        except IndexError:
            continue
        if not name or name in (".", ".."):
            continue
        result.append((name, is_dir, size_str, mtime_str))
    return result


def _parse_ls_1f(out: str) -> List[Tuple[str, bool, str, str]]:
    """Parse ls -1F output (one name per line, dirs end with '/')."""
    result = []
    for line in out.splitlines():
        name = line.strip()
        if not name or name in (".", ".."):
            continue
        is_dir = name.endswith("/")
        if is_dir:
            name = name[:-1]
        if not name:
            continue
        result.append((name, is_dir, "-", "-"))
    return result


def list_dir(serial: str, path: str, timeout: int = ADB_SHELL_TIMEOUT) -> Tuple[Optional[List[Tuple[str, bool, str, str]]], str]:
    """
    List contents of directory on device.

    Returns ([(name, is_dir, size_str, mtime_str), ...], error_msg).
    Tries ls -la first; if no entries parsed, falls back to ls -1F / ls -1.
    """
    path = _norm_path(path)
    cmd = "ls -la '%s'" % _escape_path(path)
    code, out, err = adb.shell(serial, cmd, timeout=timeout)
    if code != 0:
        return None, (err or out or "ls failed (code %s)" % code)

    result = _parse_ls_la(out)
    if not result:
        for try_cmd in ("ls -1F '%s'", "ls -1 '%s'"):
            cmd2 = try_cmd % _escape_path(path)
            code2, out2, err2 = adb.shell(serial, cmd2, timeout=timeout)
            if code2 == 0 and out2.strip():
                result = _parse_ls_1f(out2) if "F" in try_cmd else [
                    (n.strip(), False, "-", "-") for n in out2.splitlines() if n.strip() and n.strip() not in (".", "..")
                ]
                if result:
                    break
    return result, ""


def mkdir(serial: str, path: str, timeout: int = ADB_SHELL_TIMEOUT) -> Tuple[bool, str]:
    """Create directory on device. Path must be absolute."""
    path = _norm_path(path)
    cmd = "mkdir -p '%s'" % _escape_path(path)
    code, out, err = adb.shell(serial, cmd, timeout=timeout)
    if code == 0:
        return True, ""
    return False, (err or out or "mkdir failed (code %s)" % code)


def rm(serial: str, path: str, timeout: int = ADB_SHELL_TIMEOUT) -> Tuple[bool, str]:
    """Delete file or directory on device."""
    path = _norm_path(path)
    if path == ROOT or not path.startswith(ROOT + "/"):
        return False, "Refusing to delete root or invalid path"
    cmd = "rm -rf '%s'" % _escape_path(path)
    code, out, err = adb.shell(serial, cmd, timeout=timeout)
    if code == 0:
        return True, ""
    return False, (err or out or "rm failed (code %s)" % code)


def rename(serial: str, dir_path: str, old_name: str, new_name: str, timeout: int = ADB_SHELL_TIMEOUT) -> Tuple[bool, str]:
    """Rename a file/dir under dir_path on device."""
    dir_path = _norm_path(dir_path)
    if not old_name or not new_name or old_name in (".", "..") or new_name in (".", ".."):
        return False, "Invalid name"
    old_full = dir_path + "/" + old_name
    new_full = dir_path + "/" + new_name
    cmd = "mv '%s' '%s'" % (_escape_path(old_full), _escape_path(new_full))
    code, out, err = adb.shell(serial, cmd, timeout=timeout)
    if code == 0:
        return True, ""
    return False, (err or out or "mv failed (code %s)" % code)


def download(serial: str, remote_path: str, local_path: str, timeout: int = ADB_PULL_PUSH_TIMEOUT) -> Tuple[bool, str]:
    """Download from device to host."""
    remote_path = _norm_path(remote_path)
    return adb.pull(serial, remote_path, local_path, timeout=timeout)


def upload(serial: str, local_path: str, remote_dir: str, timeout: int = ADB_PULL_PUSH_TIMEOUT) -> Tuple[bool, str]:
    """Upload from host to given directory on device."""
    remote_dir = _norm_path(remote_dir)
    return adb.push(serial, local_path, remote_dir, timeout=timeout)


def get_path_size(serial: str, path: str, timeout: int = ADB_SHELL_TIMEOUT) -> int:
    """
    Best-effort size in bytes for a file or directory on device.

    Tries `du -sb` first (BusyBox or GNU), then `stat -c %s` for files.
    Returns 0 on failure.
    """
    path = _norm_path(path)
    # Try du -sb (BusyBox/GNU)
    code, out, _ = adb.shell(serial, f"du -sb '{_escape_path(path)}' 2>/dev/null", timeout=timeout)
    if code == 0 and out.strip():
        first = out.splitlines()[0].strip().split()[0]
        try:
            return int(first)
        except (ValueError, IndexError):
            pass
    # Fallback: stat for single file
    code, out, _ = adb.shell(serial, f"stat -c %s '{_escape_path(path)}' 2>/dev/null", timeout=timeout)
    if code == 0 and out.strip():
        try:
            return int(out.strip().split()[0])
        except (ValueError, IndexError):
            pass
    return 0


def format_sdcard(serial: str, timeout: int = ADB_SHELL_TIMEOUT) -> Tuple[bool, str]:
    """
    Format SD card partition and remount it on /mnt/sdcard.

    WARNING: this erases all data on /dev/mmcblk1p1. Caller must confirm with user.
    """
    cmd = (
        "umount /mnt/sdcard 2>/dev/null && "
        "mkfs.vfat -F 32 -n \"RoboWrist\" /dev/mmcblk1p1 2>/dev/null && "
        "mkdir -p /mnt/sdcard && "
        "mount /dev/mmcblk1p1 /mnt/sdcard"
    )
    code, out, err = adb.shell(serial, cmd, timeout=timeout)
    if code == 0:
        return True, (out or "SD card formatted and remounted.")
    return False, (err or out or "Format failed (code %s)" % code)
