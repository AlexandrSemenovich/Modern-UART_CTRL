@echo off
REM Forwarding to scripts\run.bat (keeps root tidy)
IF EXIST "%~dp0scripts\run.bat" (
    pushd "%~dp0"
    call scripts\run.bat %*
    popd
) ELSE (
    echo scripts\run.bat not found. Falling back to src\main.py
    python src\main.py %*
)
