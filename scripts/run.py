#!/usr/bin/env python3
"""
Launcher script for UART Control Application (moved to scripts/)
Run: python scripts/run.py
"""

import sys
import os
import subprocess


def _venv_python(project_root: str) -> str | None:
    scripts_dir = os.path.join(project_root, 'venv', 'Scripts')
    executable = os.path.join(scripts_dir, 'python.exe')
    if os.path.exists(executable):
        return executable
    bin_dir = os.path.join(project_root, 'venv', 'bin')
    executable = os.path.join(bin_dir, 'python')
    return executable if os.path.exists(executable) else None


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_python = _venv_python(project_root)
    if not venv_python:
        print("Error: Virtual environment not found! Create it with: python -m venv venv")
        return 1

    print("Starting UART Control Application...")
    cmd = [venv_python, '-m', 'src.main']
    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
        return 0
    except Exception as exc:
        print(f"Error launching application: {exc}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
