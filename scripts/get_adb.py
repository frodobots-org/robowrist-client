# -*- coding: utf-8 -*-
"""
自动下载 Android platform-tools（含 adb）到 adb/<platform>/。
仅使用标准库，无需额外依赖。
"""
from __future__ import print_function

import os
import sys
import zipfile
import tempfile
import shutil
import ssl
import time

# 项目根目录（脚本在 scripts/ 下）
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# 主源 + 备选镜像（主源失败时依次尝试）
PLATFORM_URLS = {
    "windows": [
        "https://dl.google.com/android/repository/platform-tools-latest-windows.zip",
        "https://mirrors.cloud.tencent.com/android/repository/platform-tools-latest-windows.zip",
    ],
    "darwin": [
        "https://dl.google.com/android/repository/platform-tools-latest-darwin.zip",
        "https://mirrors.cloud.tencent.com/android/repository/platform-tools-latest-darwin.zip",
    ],
    "linux": [
        "https://dl.google.com/android/repository/platform-tools-latest-linux.zip",
        "https://mirrors.cloud.tencent.com/android/repository/platform-tools-latest-linux.zip",
    ],
}

# Windows 下 adb.exe 依赖同目录的 DLL
WINDOWS_FILES = ["adb.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll"]
DOWNLOAD_TIMEOUT = 120
RETRY_COUNT = 3
RETRY_DELAY = 2


def get_platform():
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "darwin"
    return "linux"


def download(url, dest_path):
    try:
        from urllib.request import urlopen, Request
    except ImportError:
        from urllib2 import urlopen, Request
    # 使用默认 SSL 上下文，避免部分环境证书报错
    ctx = ssl.create_default_context()
    req = Request(url, headers={"User-Agent": "Robowrist-ControlCenter/1.0"})
    with urlopen(req, timeout=DOWNLOAD_TIMEOUT, context=ctx) as resp:
        with open(dest_path, "wb") as f:
            shutil.copyfileobj(resp, f)


def main():
    plat = get_platform()
    urls = PLATFORM_URLS.get(plat)
    if not urls:
        print("Unsupported platform: %s" % sys.platform)
        sys.exit(1)

    out_dir = os.path.join(ROOT, "adb", plat)
    os.makedirs(out_dir, exist_ok=True)

    if plat == "windows":
        check = os.path.join(out_dir, "adb.exe")
    else:
        check = os.path.join(out_dir, "adb")
    if os.path.isfile(check):
        print("ADB already exists: %s (skip download)" % check)
        return 0

    zip_path = os.path.join(tempfile.gettempdir(), "platform-tools-%s.zip" % plat)
    last_error = None
    for url in urls:
        for attempt in range(1, RETRY_COUNT + 1):
            try:
                print("Downloading platform-tools (%s) from: %s (attempt %d/%d, timeout=%ds) ..." % (
                    plat, url.split("/")[-1], attempt, RETRY_COUNT, DOWNLOAD_TIMEOUT))
                sys.stdout.flush()
                download(url, zip_path)
                if os.path.isfile(zip_path) and os.path.getsize(zip_path) > 1000:
                    last_error = None
                    break
            except Exception as e:
                last_error = e
                print("  Failed: %s" % e)
                sys.stdout.flush()
                if attempt < RETRY_COUNT:
                    time.sleep(RETRY_DELAY)
            else:
                break
        if last_error is None:
            break
        print("Trying next mirror...")
        sys.stdout.flush()

    if last_error is not None or not os.path.isfile(zip_path):
        print("Download failed after all retries and mirrors. Last error: %s" % (last_error or "no file"))
        sys.exit(2)

    print("Extracting to %s ..." % out_dir)
    sys.stdout.flush()
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            if plat == "windows":
                for n in names:
                    if n.endswith("/"):
                        continue
                    base = os.path.basename(n)
                    if base in WINDOWS_FILES:
                        data = zf.read(n)
                        with open(os.path.join(out_dir, base), "wb") as f:
                            f.write(data)
            else:
                tmp_extract = os.path.join(tempfile.gettempdir(), "platform-tools-extract-%s" % plat)
                if os.path.isdir(tmp_extract):
                    shutil.rmtree(tmp_extract)
                zf.extractall(tmp_extract)
                pt = os.path.join(tmp_extract, "platform-tools")
                adb_src = os.path.join(pt, "adb")
                if not os.path.isfile(adb_src):
                    for f in os.listdir(pt):
                        if f == "adb":
                            adb_src = os.path.join(pt, f)
                            break
                if os.path.isfile(adb_src):
                    shutil.copy2(adb_src, os.path.join(out_dir, "adb"))
                    os.chmod(os.path.join(out_dir, "adb"), 0o755)
                else:
                    print("adb binary not found in archive")
                    sys.exit(3)
                shutil.rmtree(tmp_extract, ignore_errors=True)
    except Exception as e:
        print("Extract failed: %s" % e)
        sys.exit(3)
    finally:
        if os.path.isfile(zip_path):
            try:
                os.remove(zip_path)
            except Exception:
                pass

    print("ADB ready: %s" % out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
