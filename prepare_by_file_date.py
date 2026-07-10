#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INCOMING = ROOT / "incoming"
UPLOADS = ROOT / "daily_uploads"
SAMPLE_NAME = "Varg_1_Chemistry_Weekly_Combined_-_Basic_Concepts_and_Atomic_Structure_Week_1_Weekly_Combined_42_CHEMISTRY_LAW.html"
MAX_FILES_PER_RUN = 15


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def remove_sample() -> int:
    removed = 0
    if UPLOADS.exists():
        for p in UPLOADS.rglob(SAMPLE_NAME):
            try:
                p.unlink()
                print(f"Sample removed: {p.relative_to(ROOT)}")
                removed += 1
            except FileNotFoundError:
                pass
        # Remove empty date folders left behind by the sample.
        for d in sorted((p for p in UPLOADS.iterdir() if p.is_dir()), reverse=True):
            try:
                next(d.iterdir())
            except StopIteration:
                d.rmdir()
                print(f"Empty folder removed: {d.relative_to(ROOT)}")
    return removed


def unique_target(dest: Path, name: str, src: Path) -> tuple[Path, bool]:
    target = dest / name
    if not target.exists():
        return target, False
    try:
        if target.stat().st_size == src.stat().st_size and sha256(target) == sha256(src):
            return target, True
    except OSError:
        pass
    stem, suffix = Path(name).stem, Path(name).suffix
    n = 2
    while True:
        candidate = dest / f"{stem}-{n}{suffix}"
        if not candidate.exists():
            return candidate, False
        n += 1


def main() -> int:
    INCOMING.mkdir(parents=True, exist_ok=True)
    UPLOADS.mkdir(parents=True, exist_ok=True)
    remove_sample()

    files = sorted(INCOMING.glob("*.html"), key=lambda p: (p.stat().st_mtime, p.name.lower()))
    if len(files) > MAX_FILES_PER_RUN:
        print(f"ERROR: incoming में {len(files)} HTML files हैं। एक run में अधिकतम {MAX_FILES_PER_RUN} रखें।")
        return 1

    if not files:
        print("incoming में नई HTML file नहीं मिली। Existing files से portal rebuild किया जा रहा है।")
    else:
        print("\nFiles को Windows 'Date modified' के अनुसार arrange किया जा रहा है:")

    for src in files:
        # Windows copy usually preserves Date modified; creation time may change during copy/extract.
        file_day = datetime.fromtimestamp(src.stat().st_mtime).strftime("%Y-%m-%d")
        dest = UPLOADS / file_day
        dest.mkdir(parents=True, exist_ok=True)
        target, identical = unique_target(dest, src.name, src)
        if identical:
            src.unlink()
            print(f"Already present, incoming copy removed: {target.relative_to(ROOT)}")
            continue
        shutil.move(str(src), str(target))
        print(f"{file_day}  ->  {target.name}")

    cmd = [sys.executable, str(ROOT / "build_site.py")]
    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
