@echo off
title Gekko
cd /d "%~dp0"

REM Use local venv if available, otherwise fall back to system Python
if exist ".venv\Scripts\python.exe" (
    set PYTHON=.venv\Scripts\python.exe
) else (
    echo Local environment not found. Running setup...
    echo.
    call setup.bat
    if not exist ".venv\Scripts\python.exe" (
        echo Setup failed. Please run setup.bat manually.
        pause
        exit /b 1
    )
    set PYTHON=.venv\Scripts\python.exe
)

%PYTHON% server.py
pause
