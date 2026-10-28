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

if not defined PYTHON_CMD if exist "%LOCALAPPDATA%\Python\pythoncore-3.13-64\python.exe" set "PYTHON_CMD=%LOCALAPPDATA%\Python\pythoncore-3.13-64\python.exe"

if not defined PYTHON_CMD (
    echo Python 3.11 or newer is required. Install Python and run setup.bat again.
    pause
    exit /b 1
)

%PYTHON_CMD% -m venv .venv
if errorlevel 1 exit /b 1

.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo Setup complete. Run run.bat to start SKM Importer.
pause