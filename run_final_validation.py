"""Wrapper: run `tests/test_final_validation.py` via pytest.
This file replaces the old `test_final_validation.py` root script to avoid pytest collection collisions.
"""
import sys
import os
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
TEST = os.path.join('tests', 'test_final_validation.py')

if __name__ == '__main__':
    rc = subprocess.run([sys.executable, '-m', 'pytest', '-q', TEST], cwd=ROOT).returncode
    sys.exit(rc)
