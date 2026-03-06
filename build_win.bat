@echo off
cd /d "%~dp0"

echo ========================================
echo   Robowrist-client - build
echo   (everything stays inside project directory)
echo ========================================
echo.

set "VENV=.venv"
set "PIP=%VENV%\Scripts\pip.exe"
set "PY=%VENV%\Scripts\python.exe"
set "PYINSTALLER=%VENV%\Scripts\pyinstaller.exe"

echo [0/4] Creating local virtualenv .venv ...
if not exist "%VENV%\Scripts\python.exe" (
    python -m venv "%VENV%"
    if %ERRORLEVEL% neq 0 (
        echo Failed to create virtualenv. Make sure Python is installed and on PATH.
        pause
        exit /b 1
    )
    echo     Created %VENV%
) else (
    echo     Already exists, skipping
)
echo.

echo [1/4] Installing dependencies into .venv (PyQt5, ntplib, PyInstaller)...
"%PIP%" install -q -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)
echo     Done.
echo.

echo [2/4] Downloading ADB into adb\ directory...
"%PY%" scripts\get_adb.py
if %ERRORLEVEL% neq 0 (
    echo Failed to download or extract ADB.
    pause
    exit /b 2
)
echo.

echo [3/4] Building application into dist\ ...
"%PYINSTALLER%" --clean -y build.spec
if %ERRORLEVEL% neq 0 (
    echo Build failed.
    pause
    exit /b 3
)
echo.

echo [4/4] Copying ADB into dist\adb ...
if not exist "dist\adb" mkdir "dist\adb"
xcopy /E /I /Y "adb\*" "dist\adb\" >nul
echo     Done.
echo.

echo ========================================
echo   All done. (Everything is inside the project directory)
echo   - Python deps: %VENV%\
echo   - ADB:         adb\windows\
echo   - Build cache: build\
echo   - Output:      dist\Robowrist-client.exe
echo   Zip the dist directory and share it with end users.
echo ========================================
echo.
pause
