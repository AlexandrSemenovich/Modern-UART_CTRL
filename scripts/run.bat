@echo off
REM Launcher script for UART Control Application (moved to scripts) on Windows

setlocal enabledelayedexpansion
set SCRIPT_DIR=%~dp0
if not exist "%SCRIPT_DIR%..\venv" (
    echo Error: Virtual environment not found!
    echo Please create it with: python -m venv venv
    pause
    exit /b 1
)

cd /d "%SCRIPT_DIR%.."
call venv\Scripts\activate.bat
python src\main.py

pause
