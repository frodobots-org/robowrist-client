#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "========================================"
echo "  Robowrist-client - build (Linux)"
echo "  (everything stays inside project directory)"
echo "========================================"
echo ""

VENV=".venv"
PIP="$VENV/bin/pip"
PY="$VENV/bin/python"
PYINSTALLER="$VENV/bin/pyinstaller"

echo "[0/4] Creating local virtualenv .venv ..."
if [ ! -f "$VENV/bin/python" ]; then
    python3 -m venv "$VENV"
    echo "      Created $VENV"
else
    echo "      Already exists, skipping"
fi
echo ""

echo "[1/4] Installing dependencies into .venv (PyQt5, ntplib, PyInstaller)..."
"$PIP" install -q -r requirements.txt
echo "      Done."
echo ""

echo "[2/4] Downloading ADB into adb/ directory..."
"$PY" scripts/get_adb.py
echo ""

echo "[3/4] Building application into dist/ ..."
"$PYINSTALLER" --clean -y build.spec
echo ""

echo "[4/4] Copying ADB into dist/adb ..."
mkdir -p dist/adb
cp -R adb/* dist/adb/
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
