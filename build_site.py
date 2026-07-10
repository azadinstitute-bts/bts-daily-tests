#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
UPLOADS = ROOT / "daily_uploads"
SITE = ROOT / "docs"
BRAND = "Bilaspur Test Series"
SUPPORT = "9981957779 | 9669946966"
WEBSITE = "bilaspurtestseries.com"

# This source pattern is retained in daily_uploads. It is replaced only in the built web copy.
LOOKBEHIND_LINE = "t=t.replace(/(?<!Go to )(?<!जाएँ )\\s+((?:Step|चरण)\\s*[-–]?\\s*[1-9१-९]\\s*[:：\\]\\)])/gi,'\\n$1 ');"
COMPAT_LINE = "t=t.replace(/\\s+((?:Step|चरण)\\s*[-–]?\\s*[1-9१-९]\\s*[:：\\]\\)])/gi,function(m,p1,offset,str){var before=str.slice(Math.max(0,offset-6),offset);if(/(?:Go to |जाएँ )$/i.test(before))return m;return '\\n'+p1+' ';});"

@dataclass
class TestItem:
    date: str
    source: Path
    output_name: str
    title: str
    subject: str
    topic: str
    test_code: str
    patched: bool


def js_string(text: str, name: str) -> str:
    pattern = rf"\b(?:const|let|var)\s+{re.escape(name)}\s*=\s*(['\"])(.*?)\1\s*;"
    m = re.search(pattern, text, re.S)
    return html.unescape(m.group(2)).strip() if m else ""


def html_title(text: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    return html.unescape(re.sub(r"\s+", " ", m.group(1)).strip()) if m else ""


def clean_display_title(raw: str) -> str:
    raw = raw.replace("_", " ")
    raw = re.sub(r"\s+", " ", raw).strip(" -_")
    raw = re.sub(r"\b([A-Za-z]+)\s+-\s+", r"\1 – ", raw)
    return raw or "Online Test"


def slugify(value: str) -> str:
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return (value[:90].rstrip("-") or "test") + ".html"


def inject_noindex(text: str) -> str:
    if re.search(r'<meta\s+name=["\']robots["\']', text, re.I):
        return text
    marker = '<meta name="robots" content="noindex,nofollow,noarchive">'
    return re.sub(r"(<head[^>]*>)", r"\1" + marker, text, count=1, flags=re.I)


def make_compatible(text: str) -> tuple[str, bool]:
    patched = False
    if LOOKBEHIND_LINE in text:
        text = text.replace(LOOKBEHIND_LINE, COMPAT_LINE)
        patched = True
    text = inject_noindex(text)
    return text, patched


def scan_tests() -> list[TestItem]:
    items: list[TestItem] = []
    used: set[tuple[str, str]] = set()
    if not UPLOADS.exists():
        return items
    for day_dir in sorted((p for p in UPLOADS.iterdir() if p.is_dir()), reverse=True):
        try:
            datetime.strptime(day_dir.name, "%Y-%m-%d")
        except ValueError:
            continue
        for source in sorted(day_dir.glob("*.html")):
            text = source.read_text(encoding="utf-8-sig", errors="replace")
            test_title = js_string(text, "TEST_TITLE") or html_title(text) or source.stem
            subject = js_string(text, "SUBJECT_NAME")
            topic = js_string(text, "TOPIC_NAME")
            code = js_string(text, "TEST_CODE")
            title = clean_display_title(test_title)
            base = slugify(code or test_title or source.stem)
            stem, suffix = Path(base).stem, Path(base).suffix
            output_name = base
            n = 2
            while (day_dir.name, output_name) in used:
                output_name = f"{stem}-{n}{suffix}"
                n += 1
            used.add((day_dir.name, output_name))
            _, patched = make_compatible(text)
            items.append(TestItem(day_dir.name, source, output_name, title, subject, topic, code, patched))
    return items


def page_shell(title: str, body: str, rel_prefix: str = "") -> str:
    safe_title = html.escape(title)
    return f'''<!doctype html>
<html lang="hi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="noindex,nofollow,noarchive">
<title>{safe_title}</title>
<style>
:root{{--navy:#0f172a;--blue:#1d4ed8;--blue2:#4338ca;--green:#15803d;--bg:#f3f6fb;--line:#dbe3ef;--muted:#64748b}}
*{{box-sizing:border-box}}html{{background:var(--bg)}}body{{margin:0;font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;color:var(--navy);background:linear-gradient(145deg,#eef2ff,#f8fafc 48%,#eff6ff);min-height:100vh}}a{{color:inherit}}.wrap{{max-width:980px;margin:auto;padding:16px 12px 70px}}.hero{{background:linear-gradient(135deg,#312e81,#4338ca 55%,#2563eb);color:white;border-radius:24px;padding:24px 18px;box-shadow:0 18px 50px #312e8130;position:relative;overflow:hidden}}.hero:after{{content:"";position:absolute;width:220px;height:220px;border-radius:50%;right:-80px;bottom:-130px;background:#ffffff18}}.brand{{font-weight:950;font-size:clamp(24px,6vw,38px);letter-spacing:.5px;position:relative;z-index:1}}.sub{{margin-top:6px;opacity:.92;font-weight:750;position:relative;z-index:1}}.meta{{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px;position:relative;z-index:1}}.chip{{display:inline-flex;border:1px solid #ffffff55;background:#ffffff18;border-radius:999px;padding:6px 10px;font-size:12px;font-weight:800}}.toolbar{{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:18px 2px 10px;flex-wrap:wrap}}h1,h2,h3,p{{margin-top:0}}.toolbar h1{{font-size:21px;margin:0}}.toolbar a{{font-size:13px;font-weight:850;color:#1d4ed8;text-decoration:none}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}}.card{{background:#fff;border:1px solid var(--line);border-radius:18px;padding:15px;box-shadow:0 8px 24px #0f172a0d;display:flex;flex-direction:column;min-height:185px}}.num{{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:11px;background:#eef2ff;color:#3730a3;font-weight:950;margin-bottom:10px}}.subject{{font-size:12px;color:#1d4ed8;font-weight:900;margin-bottom:5px}}.title{{font-weight:900;line-height:1.45;font-size:16px;margin-bottom:8px}}.topic{{font-size:12px;color:var(--muted);line-height:1.45;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}.start{{display:block;margin-top:auto;text-align:center;text-decoration:none;background:linear-gradient(135deg,#15803d,#16a34a);color:#fff;padding:11px 12px;border-radius:12px;font-weight:950;box-shadow:0 8px 18px #15803d22}}.empty{{background:#fff;border:1px dashed #cbd5e1;border-radius:18px;padding:28px;text-align:center;color:var(--muted)}}.date-list{{display:grid;gap:10px}}.date-row{{display:flex;justify-content:space-between;align-items:center;gap:12px;background:#fff;border:1px solid var(--line);border-radius:15px;padding:14px;text-decoration:none;box-shadow:0 6px 18px #0f172a0b}}.date-row b{{color:#1d4ed8}}.notice{{background:#fff7ed;border:1px solid #fed7aa;border-radius:15px;padding:12px 14px;font-size:13px;line-height:1.55;margin-top:14px;color:#7c2d12}}.footer{{margin-top:24px;text-align:center;color:var(--muted);font-size:12px;line-height:1.6}}@media(max-width:680px){{.grid{{grid-template-columns:1fr}}.wrap{{padding:9px 8px 60px}}.hero{{border-radius:18px;padding:19px 14px}}.card{{min-height:0}}}}@media(prefers-reduced-motion:reduce){{*{{scroll-behavior:auto!important}}}}
</style>
</head>
<body><main class="wrap">{body}<footer class="footer">{BRAND}<br>{WEBSITE} · सहायता: {SUPPORT}</footer></main></body></html>'''


def format_day(date_s: str) -> str:
    d = datetime.strptime(date_s, "%Y-%m-%d")
    months = ["जनवरी","फ़रवरी","मार्च","अप्रैल","मई","जून","जुलाई","अगस्त","सितंबर","अक्टूबर","नवंबर","दिसंबर"]
    return f"{d.day} {months[d.month-1]} {d.year}"


def hero(day: str, count: int, prefix: str = "") -> str:
    return f'''<section class="hero"><div class="brand">BILASPUR TEST SERIES</div><div class="sub">Daily Online Test Portal</div><div class="meta"><span class="chip">📅 {html.escape(format_day(day))}</span><span class="chip">📝 {count} Tests Available</span><span class="chip">📱 iPhone Web Compatible Build</span></div></section>'''


def card_html(item: TestItem, idx: int, href: str) -> str:
    subject = html.escape(item.subject or "Online Test")
    title = html.escape(item.title)
    topic = html.escape(item.topic or "Test खोलकर विवरण देखें।")
    return f'''<article class="card"><div class="num">{idx:02d}</div><div class="subject">{subject}</div><div class="title">{title}</div><div class="topic">{topic}</div><a class="start" href="{href}">Start Test →</a></article>'''


def build() -> int:
    items = scan_tests()
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    (SITE / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")

    grouped: dict[str, list[TestItem]] = {}
    manifest = []
    for item in items:
        grouped.setdefault(item.date, []).append(item)
        out_dir = SITE / "tests" / item.date
        out_dir.mkdir(parents=True, exist_ok=True)
        source_text = item.source.read_text(encoding="utf-8-sig", errors="replace")
        built_text, patched = make_compatible(source_text)
        (out_dir / item.output_name).write_text(built_text, encoding="utf-8")
        manifest.append({"date": item.date, "title": item.title, "subject": item.subject, "topic": item.topic, "file": f"tests/{item.date}/{item.output_name}", "iphone_compat_patch": patched})

    dates = sorted(grouped, reverse=True)
    if dates:
        latest = dates[0]
        latest_items = grouped[latest]
        cards = "".join(card_html(x, i, f"tests/{quote(latest)}/{quote(x.output_name)}") for i, x in enumerate(latest_items, 1))
        body = hero(latest, len(latest_items)) + f'''<div class="toolbar"><h1>आज के टेस्ट</h1><a href="archive.html">पुराने टेस्ट देखें →</a></div><section class="grid">{cards}</section><div class="notice"><b>निर्देश:</b> Test को WhatsApp/Files preview में नहीं, इसी web page के Start Test button से खोलें। Page refresh न करें।</div>'''
        index = page_shell(f"{BRAND} — {format_day(latest)}", body)
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        body = hero(today, 0) + '<div class="toolbar"><h1>आज के टेस्ट</h1></div><div class="empty">अभी कोई test upload नहीं किया गया है।</div>'
        index = page_shell(BRAND, body)
    (SITE / "index.html").write_text(index, encoding="utf-8")

    date_rows = []
    for date_s in dates:
        day_dir = SITE / "day" / date_s
        day_dir.mkdir(parents=True, exist_ok=True)
        tests = grouped[date_s]
        cards = "".join(card_html(x, i, f"../../tests/{quote(date_s)}/{quote(x.output_name)}") for i, x in enumerate(tests, 1))
        body = hero(date_s, len(tests)) + f'''<div class="toolbar"><h1>{html.escape(format_day(date_s))}</h1><a href="../../archive.html">← Archive</a></div><section class="grid">{cards}</section>'''
        (day_dir / "index.html").write_text(page_shell(f"Tests — {format_day(date_s)}", body), encoding="utf-8")
        date_rows.append(f'<a class="date-row" href="day/{date_s}/"><span><b>{html.escape(format_day(date_s))}</b><br><small>{len(tests)} tests</small></span><strong>खोलें →</strong></a>')
    archive_body = '''<section class="hero"><div class="brand">TEST ARCHIVE</div><div class="sub">Bilaspur Test Series</div></section><div class="toolbar"><h1>दिनांक के अनुसार</h1><a href="index.html">आज के टेस्ट →</a></div><section class="date-list">''' + ("".join(date_rows) if date_rows else '<div class="empty">Archive खाली है।</div>') + '</section>'
    (SITE / "archive.html").write_text(page_shell("Test Archive", archive_body), encoding="utf-8")
    (SITE / "404.html").write_text(page_shell("Page नहीं मिला", '<section class="hero"><div class="brand">404</div><div class="sub">यह test link उपलब्ध नहीं है।</div></section><div class="toolbar"><a href="index.html">← Test portal पर जाएँ</a></div>'), encoding="utf-8")
    (SITE / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Built {len(items)} test(s) across {len(dates)} day(s) into {SITE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
