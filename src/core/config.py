import os
import sys

# Default NTP servers
DEFAULT_NTP_SERVERS = [
    "pool.ntp.org",
    "time.windows.com",
    "ntp.aliyun.com",
]

# Timeouts (seconds)
NTP_TIMEOUT = 5
ADB_DEVICES_TIMEOUT = 10
ADB_SHELL_TIMEOUT = 15
ADB_PULL_PUSH_TIMEOUT = 300  # large file transfers


def get_platform() -> str:
    """Return 'windows' | 'macos' | 'linux'."""
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


def get_app_root() -> str:
    """Return application root directory.

    During development this is the project root;
    when frozen it is the directory containing the executable.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_bundled_adb_dir() -> str:
    """Return directory where bundled adb is located (per-platform subdir)."""
    root = get_app_root()
    plat = get_platform()
    return os.path.join(root, "adb", plat)


def get_adb_executable() -> str:
    """Return adb executable path, falling back to 'adb' in PATH."""
    bundled = get_bundled_adb_dir()
    if get_platform() == "windows":
        path = os.path.join(bundled, "adb.exe")
    else:
        path = os.path.join(bundled, "adb")
    if os.path.isfile(path):
        return path
    return "adb"
