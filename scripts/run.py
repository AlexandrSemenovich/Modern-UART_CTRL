#!/usr/bin/env python3
"""
Launcher script for UART Control Application (moved to scripts/)
Run: python scripts/run.py
"""

import sys
import os
import subprocess

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_path = os.path.join(project_root, 'venv')
    if not os.path.exists(venv_path):
        print("Error: Virtual environment not found!")
        print("Please create it with: python -m venv venv")
        return 1

    app_path = os.path.join(project_root, 'src', 'main.py')
    if not os.path.exists(app_path):
        print(f"Error: Application file not found at {app_path}")
        return 1

    print("Starting UART Control Application...")
    try:
        result = subprocess.run([sys.executable, app_path], cwd=project_root)
        return result.returncode
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
        return 0
    except Exception as e:
        print(f"Error launching application: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
