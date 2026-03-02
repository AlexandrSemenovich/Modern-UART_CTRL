@echo off
setlocal enabledelayedexpansion

REM Simple Windows build script for Modern UART Control using PyInstaller spec.
REM Usage: packaging\build_windows.bat

set ROOT=%~dp0..
set VENV=%ROOT%\.venv
if not exist "%VENV%" (
    echo [ERROR] Virtual environment not found. Please create venv first.
    exit /b 1
)

call "%VENV%\Scripts\activate.bat" || exit /b 1

echo Cleaning previous build artifacts...
if exist "%ROOT%\build" rmdir /s /q "%ROOT%\build"
if exist "%ROOT%\dist" rmdir /s /q "%ROOT%\dist"

echo Ensuring PyInstaller is available...
"%VENV%\Scripts\python.exe" -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    "%VENV%\Scripts\python.exe" -m pip install --upgrade pyinstaller || exit /b 1
)

"%VENV%\Scripts\python.exe" -m PyInstaller --clean --noconfirm packaging\OrbSterm.spec || exit /b 1

echo.
echo Build finished. Dist folder: %ROOT%\dist
deactivate
