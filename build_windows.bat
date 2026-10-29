@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3"

if not defined PYTHON_CMD (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD if exist "%LOCALAPPDATA%\Python\pythoncore-3.13-64\python.exe" set PYTHON_CMD="%LOCALAPPDATA%\Python\pythoncore-3.13-64\python.exe"

if not defined PYTHON_CMD (
    echo Python 3.11 or newer is required. Install Python and run build_windows.bat again.
    pause
    exit /b 1
)

%PYTHON_CMD% -c "import sys; sys.exit(sys.version_info < (3, 11))"
if errorlevel 1 (
    echo Python 3.11 or newer is required. Install a supported version and try again.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto failed
)

.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m pip install -r requirements-build.txt
if errorlevel 1 goto failed
.venv\Scripts\python.exe scripts\build_windows.py
if errorlevel 1 goto failed

echo.
echo Build complete: dist\SKM-Importer.exe
pause
exit /b 0

:failed
echo.
echo Build failed. Review the error above and try again.
pause
exit /b 1