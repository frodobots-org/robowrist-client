@echo off
cd /d "%~dp0"

echo ========================================
echo   Robowrist-client - build (Windows)
echo   (everything stays inside project directory)
echo ========================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python not found. Install Python 3.8+ and add it to PATH.
    echo Or visit: https://www.python.org/downloads/windows/
    pause
    exit /b 1
)

set "VENV=.venv"
set "PIP=%VENV%\Scripts\pip.exe"
set "PY=%VENV%\Scripts\python.exe"
set "PYINSTALLER=%VENV%\Scripts\pyinstaller.exe"

echo [0/5] Creating local virtualenv .venv ...
if not exist "%VENV%\Scripts\python.exe" (
    goto :create_venv
)
"%PY%" -c "exit(0)" 2>nul
if %ERRORLEVEL% neq 0 (
    echo     Existing .venv is invalid or from another path, recreating...
    rmdir /s /q "%VENV%" 2>nul
    goto :create_venv
)
echo     Already exists, skipping
goto :venv_done
:create_venv
python -m venv "%VENV%"
if %ERRORLEVEL% neq 0 (
    echo Failed to create virtualenv. Make sure Python is installed and on PATH.
    pause
    exit /b 1
)
echo     Created %VENV%
:venv_done
echo.

echo [1/5] Installing dependencies into .venv (PyQt5, ntplib, PyInstaller)...
"%PIP%" install -q -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)
echo     Done.
echo.

echo [2/5] Downloading ADB into adb\ directory...
"%PY%" scripts\get_adb.py
if %ERRORLEVEL% neq 0 (
    echo Failed to download or extract ADB.
    pause
    exit /b 2
)
echo     Done.
echo.

echo [3/5] Generating assets\icon.ico for exe icon...
"%PY%" scripts\build_icon_ico.py
echo.

echo [4/5] Building application into dist\ ...
"%PYINSTALLER%" --clean -y build.spec
if %ERRORLEVEL% neq 0 (
    echo Build failed.
    pause
    exit /b 3
)
echo     Done.
echo.

echo [5/5] Copying ADB into dist\adb ...
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
