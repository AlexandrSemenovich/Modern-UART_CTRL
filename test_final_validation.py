"""
Wrapper: run the canonical tests located under tests/ using pytest.
This keeps the root tidy while preserving the original entrypoint name.
"""
import sys
import os
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
TEST_FILE = os.path.join(ROOT, 'tests', 'test_final_validation.py')

if __name__ == '__main__':
    if os.path.exists(TEST_FILE):
        rc = subprocess.run([sys.executable, '-m', 'pytest', '-q', TEST_FILE], cwd=ROOT).returncode
        sys.exit(rc)
    else:
        print('tests/test_final_validation.py not found. Run pytest manually.')
        sys.exit(2)
