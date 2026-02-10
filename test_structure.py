"""
Wrapper: Runs canonical `tests/test_structure.py` via pytest.
"""
import os
import sys
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
TEST_FILE = os.path.join(ROOT, 'tests', 'test_structure.py')

if __name__ == '__main__':
    if os.path.exists(TEST_FILE):
        rc = subprocess.run([sys.executable, '-m', 'pytest', '-q', TEST_FILE], cwd=ROOT).returncode
        sys.exit(rc)
    else:
        print('tests/test_structure.py not found. Run pytest manually.')
        sys.exit(2)
