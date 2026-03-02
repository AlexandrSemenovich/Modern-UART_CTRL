#!/usr/bin/env python3
"""Entry point for launching UART Control from repository root."""

import os
import sys
import subprocess


def main() -> int:
    project_root = os.path.dirname(os.path.abspath(__file__))
    launcher = os.path.join(project_root, 'scripts', 'run.py')
    if not os.path.exists(launcher):
        print('Launcher not found: scripts/run.py')
        return 1
    return subprocess.run([sys.executable, launcher], cwd=project_root).returncode


if __name__ == '__main__':
    raise SystemExit(main())
