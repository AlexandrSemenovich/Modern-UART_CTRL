#!/usr/bin/env python3
"""
Lightweight wrapper: forwards to `scripts/run.py`.
"""
import sys
import os
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(ROOT, 'scripts', 'run.py')

if __name__ == '__main__':
    if os.path.exists(SCRIPT):
        sys.exit(subprocess.run([sys.executable, SCRIPT], cwd=ROOT).returncode)
    else:
        print('Launcher not found: scripts/run.py')
        sys.exit(1)
