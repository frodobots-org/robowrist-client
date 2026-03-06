"""Core package for Robowrist-client.

This file is intentionally minimal to avoid circular-import issues when
the package is loaded by PyInstaller. Import submodules explicitly, e.g.:

    import src.core.adb as adb
    import src.core.time_sync as time_sync
    import src.core.sdcard_fs as sdcard_fs
"""

__all__: list[str] = []
