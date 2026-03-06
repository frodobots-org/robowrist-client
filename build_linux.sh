#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "========================================"
echo "  Robowrist-client - build (Linux)"
echo "  (everything stays inside project directory)"
echo "========================================"
echo ""

if ! command -v python3 &>/dev/null; then
    echo "python3 not found. Install Python 3.8+ (e.g. apt install python3-venv python3-pip)."
    echo "Or visit: https://www.python.org/downloads/"
    exit 1
fi

VENV=".venv"
PIP="$VENV/bin/pip"
PY="$VENV/bin/python"
PYINSTALLER="$VENV/bin/pyinstaller"

echo "[0/5] Creating local virtualenv .venv ..."
if [ ! -f "$VENV/bin/python" ]; then
    python3 -m venv "$VENV" || { echo "Failed to create virtualenv."; exit 1; }
    echo "      Created $VENV"
else
    if ! "$PY" -c "exit(0)" 2>/dev/null; then
        echo "      Existing .venv is invalid or from another path, recreating..."
        rm -rf "$VENV"
        python3 -m venv "$VENV" || { echo "Failed to create virtualenv."; exit 1; }
        echo "      Created $VENV"
    else
        echo "      Already exists, skipping"
    fi
fi
echo ""

echo "[1/5] Installing dependencies into .venv (PyQt5, ntplib, PyInstaller)..."
"$PIP" install -q -r requirements.txt || { echo "Failed to install dependencies."; exit 1; }
echo "      Done."
echo ""

echo "[2/5] Downloading ADB into adb/ directory..."
"$PY" scripts/get_adb.py || { echo "Failed to download or extract ADB."; exit 2; }
echo "      Done."
echo ""

echo "[3/5] Generating assets/icon.ico for exe icon..."
"$PY" scripts/build_icon_ico.py
echo ""

echo "[4/5] Building application into dist/ ..."
"$PYINSTALLER" --clean -y build.spec || { echo "Build failed."; exit 3; }
echo "      Done."
echo ""

echo "[5/5] Copying ADB into dist/adb ..."
mkdir -p dist/adb
if [ -d adb ] && [ -n "$(ls -A adb 2>/dev/null)" ]; then
    cp -R adb/. dist/adb/
fi
echo "      Done."
echo ""

echo "========================================"
echo "  All done. (Everything is inside the project directory)"
echo "  - Python deps: $VENV/"
echo "  - ADB:         adb/"
echo "  - Build cache: build/"
echo "  - Output:      dist/Robowrist-client"
echo "  Zip the dist directory and share it with end users."
echo "========================================"
echo ""
