#!/usr/bin/env python3
from __future__ import annotations
import argparse
import shutil
from datetime import date, datetime
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
INCOMING = ROOT / "incoming"
UPLOADS = ROOT / "daily_uploads"

p = argparse.ArgumentParser(description="Move today's HTML tests into the dated upload folder and build preview.")
p.add_argument("--date", dest="day", default=date.today().isoformat(), help="YYYY-MM-DD; default is today")
args = p.parse_args()
try:
    datetime.strptime(args.day, "%Y-%m-%d")
except ValueError:
    raise SystemExit("Date format must be YYYY-MM-DD")

files = sorted(INCOMING.glob("*.html"))
if not files:
    raise SystemExit("incoming folder में कोई .html file नहीं मिली।")
if len(files) > 15:
    raise SystemExit(f"incoming में {len(files)} HTML files हैं। Daily limit 15 रखें या अतिरिक्त files हटाएँ।")

dest = UPLOADS / args.day
dest.mkdir(parents=True, exist_ok=True)
for src in files:
    target = dest / src.name
    if target.exists():
        raise SystemExit(f"File पहले से मौजूद है: {target.name}")
    shutil.move(str(src), str(target))
    print(f"Added: {target.relative_to(ROOT)}")

result = subprocess.run([sys.executable, str(ROOT / "build_site.py")], cwd=ROOT)
raise SystemExit(result.returncode)
