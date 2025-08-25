# src/nsi.py
"""
Scraper for NSI Bulgaria monthly release calendar pages.
- Entry point: scrape() -> List[Event]
- Strategy: discover current year pages from https://www.nsi.bg/calendar then follow monthly links.
- Each item is treated as all-day (NSI usually does not publish hours).
"""
from __future__ import annotations
from bs4 import BeautifulSoup
import requests, re
from datetime import datetime
from dateutil import parser as dateparser
from typing import List
from .common import Event

ROOT = "https://www.nsi.bg/calendar"

HEADERS = {"User-Agent": "bg-stats-ics/1.0 (+https://example.org/)"}

def fetch(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

def parse_month_page(html: str, base_url: str) -> List[Event]:
    soup = BeautifulSoup(html, "lxml")
    events: List[Event] = []

    # NSI calendar pages often have a table/list with date and title per row.
    # We'll attempt to find date strings (e.g., '15 август 2025' or '2025-08-15') and the adjacent title.
    # Fallback: look for <li> entries containing a date and text.
    def bn(text): return re.sub(r"\s+", " ", text or "").strip()

    # Try table rows
    for row in soup.select("table tr"):
        cells = row.find_all(["td", "th"])
        if len(cells) < 2:
            continue
        date_txt = bn(cells[0].get_text(" "))
        title_txt = bn(cells[1].get_text(" "))
        if not date_txt or not title_txt:
            continue
        dt = try_parse_bg_date(date_txt)
        if not dt:
            continue
        events.append(Event(
            start=dt,
            all_day=True,
            title=title_txt,
            description=f"НСИ – {date_txt}",
            url=base_url
        ))

    # Also check list items
    for li in soup.select("li"):
        t = bn(li.get_text(" "))
        # crude date detection
        m = re.search(r"(\d{1,2}\s+[А-Яа-я]+(?:\s+20\d{2})?)", t)
        if not m: 
            continue
        dt = try_parse_bg_date(m.group(1))
        if not dt:
            continue
        title = t.replace(m.group(1), "").strip(" -–:")
        if not title:
            title = t
        events.append(Event(
            start=dt,
            all_day=True,
            title=title,
            description=f"НСИ – {m.group(1)}",
            url=base_url
        ))

    # De-duplicate by (date,title)
    key = set()
    uniq = []
    for e in events:
        k = (e.start.date().isoformat(), e.title)
        if k not in key:
            key.add(k)
            uniq.append(e)
    return uniq

BG_MONTHS = {
    "януари":1,"февруари":2,"март":3,"април":4,"май":5,"юни":6,
    "юли":7,"август":8,"септември":9,"октомври":10,"ноември":11,"декември":12
}

def try_parse_bg_date(text: str):
    t = text.lower()
    # examples: 15 август 2025, 2 септември, 2025-08-15
    for name, num in BG_MONTHS.items():
        t = t.replace(name, str(num))
    t = t.replace("г.", "").replace("год.", "")
    t = re.sub(r"\s+", " ", t).strip()
    # If day and month only, add current year
    parts = t.split(" ")
    try:
        if re.match(r"\d{4}-\d{2}-\d{2}", t):
            return datetime.fromisoformat(t)
        if len(parts) == 2:  # "15 8"
            d, m = map(int, parts)
            y = datetime.now().year
            return datetime(y, m, d)
        if len(parts) == 3:  # "15 8 2025"
            d, m, y = map(int, parts)
            return datetime(y, m, d)
        # fallback
        return dateparser.parse(text, dayfirst=True, fuzzy=True)
    except Exception:
        return None

def discover_month_links(root_html: str) -> list[tuple[str,str]]:
    soup = BeautifulSoup(root_html, "lxml")
    links = []
    for a in soup.select("a[href]"):
        href = a["href"]
        txt = (a.get_text() or "").strip().lower()
        if any(m in txt for m in BG_MONTHS.keys()):
            if href.startswith("/"):
                href = "https://www.nsi.bg" + href
            links.append((a.get_text(strip=True), href))
    # Deduplicate and keep only this year
    year = str(datetime.now().year)
    out = []
    seen = set()
    for label, href in links:
        if year in href or year in label:
            if href not in seen:
                seen.add(href)
                out.append((label, href))
    return out

def scrape() -> List[Event]:
    root_html = fetch(ROOT)
    months = discover_month_links(root_html)
    all_events: List[Event] = []
    for label, url in months:
        html = fetch(url)
        evs = parse_month_page(html, url)
        all_events.extend(evs)
    # Sort and return
    all_events.sort(key=lambda e: (e.start, e.title))
    return all_events

if __name__ == "__main__":
    evs = scrape()
    print(f"NSI events: {len(evs)}")
    for e in evs[:5]:
        print(e.start.date(), e.title)
