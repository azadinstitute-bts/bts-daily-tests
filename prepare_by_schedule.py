#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INCOMING = ROOT / "incoming"
UPLOADS = ROOT / "daily_uploads"
BASE_WEEK = 1
BASE_DAY = 1
BASE_DATE = date(2026, 7, 6)  # IST schedule: Week 1 Day 1
MAX_FILES_PER_RUN = 15
SAMPLE_NAME = "Varg_1_Chemistry_Weekly_Combined_-_Basic_Concepts_and_Atomic_Structure_Week_1_Weekly_Combined_42_CHEMISTRY_LAW.html"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def js_string(text: str, name: str) -> str:
    pattern = rf"\b(?:const|let|var)\s+{re.escape(name)}\s*=\s*(['\"])(.*?)\1\s*;"
    m = re.search(pattern, text, re.S)
    return re.sub(r"\s+", " ", m.group(2)).strip() if m else ""


def html_title(text: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def extract_schedule_text(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        text = ""
    parts = [path.stem]
    if text:
        parts.append(js_string(text, "TEST_TITLE"))
        parts.append(js_string(text, "TEST_CODE"))
        parts.append(html_title(text))
    return " ".join(p for p in parts if p)


def extract_week_day(path: Path) -> tuple[int, int, str]:
    raw = extract_schedule_text(path)
    normalized = raw.replace("_", " ").replace("-", " ")
    week = None
    day = None
    wm = re.search(r"(?:\bweek\b|W)\s*[:#]?\s*(\d{1,2})", normalized, re.I)
    dm = re.search(r"(?:\bday\b|D)\s*[:#]?\s*(\d{1,2})", normalized, re.I)
    if wm:
        week = int(wm.group(1))
    if dm:
        day = int(dm.group(1))
    weekly_combined = bool(re.search(r"\bweekly\s+combined\b|\bweekly\b", normalized, re.I))
    if week is None:
        raise ValueError(f"Week number nahi mila: {path.name}")
    if day is None:
        if weekly_combined:
            day = 7
        else:
            raise ValueError(f"Day number nahi mila aur Weekly Combined bhi nahi hai: {path.name}")
    if week < 1 or day < 1 or day > 7:
        raise ValueError(f"Invalid Week/Day: Week {week}, Day {day} in {path.name}")
    label = f"Week {week} Day {day}" + (" (Weekly Combined)" if weekly_combined and day == 7 else "")
    return week, day, label


def schedule_date_for(week: int, day: int) -> date:
    offset_days = (week - BASE_WEEK) * 7 + (day - BASE_DAY)
    return BASE_DATE + timedelta(days=offset_days)


def remove_sample() -> None:
    if not UPLOADS.exists():
        return
    for p in UPLOADS.rglob(SAMPLE_NAME):
        try:
            p.unlink()
            print(f"Sample removed: {p.relative_to(ROOT)}")
        except FileNotFoundError:
            pass


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


def incoming_html_files() -> list[Path]:
    if not INCOMING.exists():
        return []
    return sorted(
        [p for p in INCOMING.iterdir() if p.is_file() and p.suffix.lower() in {".html", ".htm"}],
        key=lambda p: p.name.casefold(),
    )


def arrange_incoming(files: list[Path]) -> bool:
    if len(files) > MAX_FILES_PER_RUN:
        raise RuntimeError(f"incoming me {len(files)} HTML files hain. Ek run me maximum {MAX_FILES_PER_RUN} rakhein.")
    if not files:
        print("incoming me nayi HTML file nahi mili. Kuch publish/build nahi kiya jayega.")
        return False
    changed = False
    print("\nSchedule ke hisab se arrange ho raha hai. Modified date ignore hogi:")
    for src in files:
        week, day, label = extract_week_day(src)
        target_date = schedule_date_for(week, day).isoformat()
        dest = UPLOADS / target_date
        dest.mkdir(parents=True, exist_ok=True)
        name = src.with_suffix(".html").name
        target, identical = unique_target(dest, name, src)
        if identical:
            src.unlink()
            print(f"Already present, incoming copy removed: {target_date} | {label} | {target.name}")
            continue
        changed = True
        shutil.move(str(src), str(target))
        print(f"{target_date} | {label} -> {target.name}")
    return changed


def main() -> int:
    INCOMING.mkdir(parents=True, exist_ok=True)
    UPLOADS.mkdir(parents=True, exist_ok=True)
    remove_sample()
    try:
        changed = arrange_incoming(incoming_html_files())
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1
    if not changed:
        return 0
    result = subprocess.run([sys.executable, str(ROOT / "build_site.py")], cwd=ROOT)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

