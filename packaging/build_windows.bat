@echo off
setlocal enabledelayedexpansion

REM Simple Windows build script for Modern UART Control using PyInstaller spec.
REM Usage: packaging\build_windows.bat

set ROOT=%~dp0..
set VENV=%ROOT%\venv
if not exist "%VENV%" (
    echo [ERROR] Virtual environment not found. Please create venv first.
    exit /b 1
)

call "%VENV%\Scripts\activate.bat" || exit /b 1
pyinstaller --clean --noconfirm packaging\OrbSterm.spec || exit /b 1

echo.
echo Build finished. Dist folder: %ROOT%\dist
deactivate
