"""Package application resources into a distributable archive.

This script collects source code, configs and assets into a single
zip bundle accompanied by a manifest json. The resulting archive is
later unpacked by the custom launcher.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "build" / "resources"
ARCHIVE_PATH = OUTPUT_DIR / "resources.zip"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"


INCLUDE_PATHS = [
    (PROJECT_ROOT / "src", "src"),
    (PROJECT_ROOT / "config", "config"),
    (PROJECT_ROOT / "assets", "assets"),
    (PROJECT_ROOT / "scripts", "scripts"),
]


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()


def build_archive() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    manifest: dict[str, dict[str, str]] = {}

    with zipfile.ZipFile(ARCHIVE_PATH, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for base_path, prefix in INCLUDE_PATHS:
            if not base_path.exists():
                continue
            for file in base_path.rglob("*"):
                if file.is_file():
                    rel_path = Path(prefix) / file.relative_to(base_path)
                    zf.write(file, rel_path.as_posix())
                    manifest[rel_path.as_posix()] = {
                        "sha256": hash_file(file),
                        "size": str(file.stat().st_size),
                    }

    MANIFEST_PATH.write_text(json.dumps({"files": manifest}, indent=2), encoding="utf-8")
    print(f"Created archive: {ARCHIVE_PATH}")


if __name__ == "__main__":
    build_archive()
