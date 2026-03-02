@echo off
REM Launcher script for UART Control Application (moved to scripts) on Windows

@echo off
setlocal
set PROJECT_ROOT=%~dp0..

if exist "%PROJECT_ROOT%\venv\Scripts\python.exe" (
    set PYTHON_EXE=%PROJECT_ROOT%\venv\Scripts\python.exe
) else if exist "%PROJECT_ROOT%\venv\bin\python.exe" (
    set PYTHON_EXE=%PROJECT_ROOT%\venv\bin\python.exe
) else (
    echo Error: virtual environment not found! Create it with: python -m venv venv
    goto :eof
)

pushd "%PROJECT_ROOT%"
"%PYTHON_EXE%" -m src.main %*
set EXIT_CODE=%ERRORLEVEL%
popd

exit /b %EXIT_CODE%
