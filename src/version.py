"""
Project version helper. Reads the latest git tag (strips leading 'v')
and exposes `__version__`.
"""
import os
import subprocess

def _get_git_tag():
    try:
        root = os.path.dirname(os.path.dirname(__file__))
        tag = subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0'], cwd=root, stderr=subprocess.DEVNULL)
        return tag.decode().strip().lstrip('v')
    except Exception:
        return None

__version__ = _get_git_tag() or '0.0.0'

def get_version():
    return __version__
