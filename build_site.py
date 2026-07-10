#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import shutil
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
    week: int | None
    day: int | None
    weekly_combined: bool
    patched: bool

    @property
    def schedule_label(self) -> str:
        bits: list[str] = []
        if self.week is not None:
            bits.append(f"Week {self.week}")
        if self.day is not None:
            bits.append(f"Day {self.day}")
        elif self.weekly_combined:
            bits.append("Weekly Combined")
        return " • ".join(bits) or "Test"

    @property
    def sort_key(self) -> tuple[int, int, int, str]:
        return (
            self.week if self.week is not None else 999,
            self.day if self.day is not None else (8 if self.weekly_combined else 999),
            1 if self.weekly_combined else 0,
            self.title.casefold(),
        )


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


SAFE_STORAGE_HELPERS = "function azadSafeStorageGet(k){try{return window.localStorage?window.localStorage.getItem(k):null}catch(e){return null}}function azadSafeStorageSet(k,v){try{if(window.localStorage)window.localStorage.setItem(k,v)}catch(e){}}"


def make_compatible(text: str) -> tuple[str, bool]:
    patched = False
    if LOOKBEHIND_LINE in text:
        text = text.replace(LOOKBEHIND_LINE, COMPAT_LINE)
        patched = True

    # iPhone Safari can throw a SecurityError when storage is unavailable
    # (private mode / restricted storage). In the original export this happens
    # before the submit try/catch, so the review closes and the question page
    # reappears without any message. Use non-fatal wrappers in the web copy.
    storage_changed = False
    if "localStorage.getItem(" in text:
        text = text.replace("localStorage.getItem(", "azadSafeStorageGet(")
        storage_changed = True
    if "localStorage.setItem(" in text:
        text = text.replace("localStorage.setItem(", "azadSafeStorageSet(")
        storage_changed = True
    if storage_changed and "function azadSafeStorageGet(" not in text:
        marker = "async function submitQuiz("
        if marker in text:
            text = text.replace(marker, SAFE_STORAGE_HELPERS + marker, 1)
        else:
            text = text.replace("</script>", SAFE_STORAGE_HELPERS + "</script>", 1)
        patched = True

    # Do not leave async pre-submit failures silent on Safari. The original
    # review button closes the modal before calling submitQuiz; if the promise
    # rejects, the student otherwise lands back on the question screen.
    old_confirm = 'onclick="closeJumpBox();submitQuiz(true)"'
    new_confirm = 'onclick="closeJumpBox();submitQuiz(true).catch(function(e){showSubmitError(e,\'CLIENT_ERROR\')})"'
    if old_confirm in text:
        text = text.replace(old_confirm, new_confirm)
        patched = True

    text = inject_noindex(text)
    return text, patched


def extract_schedule(*values: str) -> tuple[int | None, int | None, bool]:
    raw = " ".join(v for v in values if v)
    normalized = raw.replace("_", " ").replace("-", " ")
    week = None
    day = None
    wm = re.search(r"(?:\bweek\b|सप्ताह)\s*[:#]?\s*(\d{1,2})", normalized, re.I)
    dm = re.search(r"(?:\bday\b|दिन)\s*[:#]?\s*(\d{1,2})", normalized, re.I)
    if not wm:
        wm = re.search(r"\bW\s*(\d{1,2})\b", normalized, re.I)
    if not dm:
        dm = re.search(r"\bD\s*(\d{1,2})\b", normalized, re.I)
    if wm:
        week = int(wm.group(1))
    if dm:
        day = int(dm.group(1))
    weekly_combined = bool(re.search(r"\bweekly\s+combined\b|साप्ताहिक\s+संयुक्त", normalized, re.I))
    return week, day, weekly_combined


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
        for source in sorted(day_dir.glob("*.html"), key=lambda p: p.name.casefold()):
            text = source.read_text(encoding="utf-8-sig", errors="replace")
            test_title = js_string(text, "TEST_TITLE") or html_title(text) or source.stem
            subject = js_string(text, "SUBJECT_NAME")
            topic = js_string(text, "TOPIC_NAME")
            code = js_string(text, "TEST_CODE")
            title = clean_display_title(test_title)
            week, test_day, weekly_combined = extract_schedule(source.stem, test_title, code)
            base = slugify(code or test_title or source.stem)
            stem, suffix = Path(base).stem, Path(base).suffix
            output_name = base
            n = 2
            while (day_dir.name, output_name) in used:
                output_name = f"{stem}-{n}{suffix}"
                n += 1
            used.add((day_dir.name, output_name))
            _, patched = make_compatible(text)
            items.append(TestItem(day_dir.name, source, output_name, title, subject, topic, code, week, test_day, weekly_combined, patched))
    return items


def page_shell(title: str, body: str) -> str:
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
*{{box-sizing:border-box}}html{{background:var(--bg)}}body{{margin:0;font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;color:var(--navy);background:linear-gradient(145deg,#eef2ff,#f8fafc 48%,#eff6ff);min-height:100vh}}a{{color:inherit}}.wrap{{max-width:980px;margin:auto;padding:16px 12px 70px}}.hero{{background:linear-gradient(135deg,#312e81,#4338ca 55%,#2563eb);color:white;border-radius:24px;padding:24px 18px;box-shadow:0 18px 50px #312e8130;position:relative;overflow:hidden}}.hero:after{{content:"";position:absolute;width:220px;height:220px;border-radius:50%;right:-80px;bottom:-130px;background:#ffffff18}}.brand{{font-weight:950;font-size:clamp(24px,6vw,38px);letter-spacing:.5px;position:relative;z-index:1}}.sub{{margin-top:6px;opacity:.92;font-weight:750;position:relative;z-index:1}}.meta{{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px;position:relative;z-index:1}}.chip{{display:inline-flex;border:1px solid #ffffff55;background:#ffffff18;border-radius:999px;padding:6px 10px;font-size:12px;font-weight:800}}.toolbar{{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:18px 2px 10px;flex-wrap:wrap}}h1,h2,h3,p{{margin-top:0}}.toolbar h1{{font-size:21px;margin:0}}.toolbar a{{font-size:13px;font-weight:850;color:#1d4ed8;text-decoration:none}}.date-section{{margin-top:18px}}.date-heading{{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:0 2px 10px}}.date-heading h2{{font-size:18px;margin:0}}.date-heading span{{font-size:12px;color:var(--muted);font-weight:800}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}}.card{{background:#fff;border:1px solid var(--line);border-radius:18px;padding:15px;box-shadow:0 8px 24px #0f172a0d;display:flex;flex-direction:column;min-height:202px}}.topline{{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:10px}}.num{{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:11px;background:#eef2ff;color:#3730a3;font-weight:950}}.schedule{{display:inline-flex;border:1px solid #bfdbfe;background:#eff6ff;color:#1e40af;border-radius:999px;padding:5px 9px;font-size:11px;font-weight:900}}.subject{{font-size:12px;color:#1d4ed8;font-weight:900;margin-bottom:5px}}.title{{font-weight:900;line-height:1.45;font-size:16px;margin-bottom:8px}}.topic{{font-size:12px;color:var(--muted);line-height:1.45;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}.start{{display:block;margin-top:auto;text-align:center;text-decoration:none;background:linear-gradient(135deg,#15803d,#16a34a);color:#fff;padding:11px 12px;border-radius:12px;font-weight:950;box-shadow:0 8px 18px #15803d22}}.empty{{background:#fff;border:1px dashed #cbd5e1;border-radius:18px;padding:28px;text-align:center;color:var(--muted)}}.date-list{{display:grid;gap:10px}}.date-row{{display:flex;justify-content:space-between;align-items:center;gap:12px;background:#fff;border:1px solid var(--line);border-radius:15px;padding:14px;text-decoration:none;box-shadow:0 6px 18px #0f172a0b}}.date-row b{{color:#1d4ed8}}.notice{{background:#fff7ed;border:1px solid #fed7aa;border-radius:15px;padding:12px 14px;font-size:13px;line-height:1.55;margin-top:14px;color:#7c2d12}}.footer{{margin-top:24px;text-align:center;color:var(--muted);font-size:12px;line-height:1.6}}@media(max-width:680px){{.grid{{grid-template-columns:1fr}}.wrap{{padding:9px 8px 60px}}.hero{{border-radius:18px;padding:19px 14px}}.card{{min-height:0}}}}@media(prefers-reduced-motion:reduce){{*{{scroll-behavior:auto!important}}}}
</style>
</head>
<body><main class="wrap">{body}<footer class="footer">{BRAND}<br>{WEBSITE} · सहायता: {SUPPORT}</footer></main></body></html>'''


def format_day(date_s: str) -> str:
    d = datetime.strptime(date_s, "%Y-%m-%d")
    months = ["जनवरी","फ़रवरी","मार्च","अप्रैल","मई","जून","जुलाई","अगस्त","सितंबर","अक्टूबर","नवंबर","दिसंबर"]
    return f"{d.day} {months[d.month-1]} {d.year}"


def hero(total: int, date_count: int) -> str:
    return f'''<section class="hero"><div class="brand">BILASPUR TEST SERIES</div><div class="sub">iPhone Students — Online Test Portal</div><div class="meta"><span class="chip">📝 {total} Tests Available</span><span class="chip">📅 {date_count} Upload Dates</span><span class="chip">📱 iPhone Web Compatible Build</span></div></section>'''


def card_html(item: TestItem, idx: int, href: str) -> str:
    subject = html.escape(item.subject or "Online Test")
    title = html.escape(item.title)
    topic = html.escape(item.topic or "Test खोलकर विवरण देखें।")
    label = html.escape(item.schedule_label)
    return f'''<article class="card"><div class="topline"><div class="num">{idx:02d}</div><div class="schedule">{label}</div></div><div class="subject">{subject}</div><div class="title">{title}</div><div class="topic">{topic}</div><a class="start" href="{href}">Start Test →</a></article>'''


def grouped_sections(grouped: dict[str, list[TestItem]], link_prefix: str = "") -> str:
    blocks: list[str] = []
    for date_s in sorted(grouped, reverse=True):
        tests = sorted(grouped[date_s], key=lambda x: x.sort_key)
        cards = "".join(
            card_html(x, i, f"{link_prefix}tests/{quote(date_s)}/{quote(x.output_name)}")
            for i, x in enumerate(tests, 1)
        )
        blocks.append(
            f'''<section class="date-section"><div class="date-heading"><h2>{html.escape(format_day(date_s))}</h2><span>{len(tests)} test(s)</span></div><div class="grid">{cards}</div></section>'''
        )
    return "".join(blocks)


def build() -> int:
    items = scan_tests()
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    (SITE / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")

    grouped: dict[str, list[TestItem]] = {}
    manifest: list[dict[str, object]] = []
    for item in items:
        grouped.setdefault(item.date, []).append(item)
        out_dir = SITE / "tests" / item.date
        out_dir.mkdir(parents=True, exist_ok=True)
        source_text = item.source.read_text(encoding="utf-8-sig", errors="replace")
        built_text, patched = make_compatible(source_text)
        (out_dir / item.output_name).write_text(built_text, encoding="utf-8")
        manifest.append({
            "date": item.date,
            "week": item.week,
            "day": item.day,
            "schedule_label": item.schedule_label,
            "title": item.title,
            "subject": item.subject,
            "topic": item.topic,
            "file": f"tests/{item.date}/{item.output_name}",
            "iphone_compat_patch": patched,
        })

    if items:
        body = hero(len(items), len(grouped)) + '<div class="toolbar"><h1>सभी उपलब्ध टेस्ट</h1><a href="archive.html">दिनांक सूची देखें →</a></div>' + grouped_sections(grouped) + '<div class="notice"><b>निर्देश:</b> Test को WhatsApp/Files preview में नहीं, इसी web page के Start Test button से खोलें। Page refresh न करें।</div>'
    else:
        body = hero(0, 0) + '<div class="toolbar"><h1>उपलब्ध टेस्ट</h1></div><div class="empty">अभी कोई test upload नहीं किया गया है।</div>'
    (SITE / "index.html").write_text(page_shell(BRAND, body), encoding="utf-8")

    date_rows: list[str] = []
    for date_s in sorted(grouped, reverse=True):
        day_dir = SITE / "day" / date_s
        day_dir.mkdir(parents=True, exist_ok=True)
        tests = sorted(grouped[date_s], key=lambda x: x.sort_key)
        cards = "".join(card_html(x, i, f"../../tests/{quote(date_s)}/{quote(x.output_name)}") for i, x in enumerate(tests, 1))
        day_body = hero(len(tests), 1) + f'''<div class="toolbar"><h1>{html.escape(format_day(date_s))}</h1><a href="../../index.html">← सभी टेस्ट</a></div><section class="grid">{cards}</section>'''
        (day_dir / "index.html").write_text(page_shell(f"Tests — {format_day(date_s)}", day_body), encoding="utf-8")
        date_rows.append(f'<a class="date-row" href="day/{date_s}/"><span><b>{html.escape(format_day(date_s))}</b><br><small>{len(tests)} tests</small></span><strong>खोलें →</strong></a>')

    archive_body = '''<section class="hero"><div class="brand">TEST ARCHIVE</div><div class="sub">Bilaspur Test Series</div></section><div class="toolbar"><h1>दिनांक के अनुसार</h1><a href="index.html">सभी टेस्ट →</a></div><section class="date-list">''' + ("".join(date_rows) if date_rows else '<div class="empty">Archive खाली है।</div>') + '</section>'
    (SITE / "archive.html").write_text(page_shell("Test Archive", archive_body), encoding="utf-8")
    (SITE / "404.html").write_text(page_shell("Page नहीं मिला", '<section class="hero"><div class="brand">404</div><div class="sub">यह test link उपलब्ध नहीं है।</div></section><div class="toolbar"><a href="index.html">← Test portal पर जाएँ</a></div>'), encoding="utf-8")
    (SITE / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Built {len(items)} test(s) across {len(grouped)} date(s) into {SITE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
