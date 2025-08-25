# src/bnb.py
"""
Scraper for BNB (Bulgarian National Bank) Press Office Calendar.
- Entry: scrape() -> List[Event]
- Uses the HTML calendar grid; parses date, time, title, and period.
"""
from __future__ import annotations
from bs4 import BeautifulSoup
import requests, re
from datetime import datetime, timedelta
from dateutil import parser as dateparser, tz
from typing import List
from .common import Event, SOFIA_TZID

ROOT = "https://www.bnb.bg/AboutUs/PressOffice/POCalendar/index.htm"
HEADERS = {"User-Agent": "bg-stats-ics/1.0 (+https://example.org/)"}

def fetch(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

def parse(html: str, base_url: str) -> List[Event]:
    soup = BeautifulSoup(html, "lxml")
    events: List[Event] = []

    # The calendar often lists items as <div class="event"> with date/time.
    # We implement multiple heuristics to be resilient.
    def bn(x): return re.sub(r"\s+", " ", (x or "")).strip()
    tzinfo = tz.gettz(SOFIA_TZID)

    # Strategy 1: look for rows with a date like "25 August 2025" and a time "12:00"
    date_nodes = soup.find_all(string=re.compile(r"\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December|януари|февруари|март|април|май|юни|юли|август|септември|октомври|ноември|декември)\b", re.I))
    for node in date_nodes:
        container = node.find_parent()
        if not container:
            continue
        # find a time nearby
        tnode = container.find(string=re.compile(r"\b\d{1,2}:\d{2}\b"))
        title_node = container.find_next(["a","strong","b","span"])
        try:
            dt_date = dateparser.parse(str(node), dayfirst=True, fuzzy=True)
        except Exception:
            dt_date = None
        if dt_date and title_node:
            title = bn(title_node.get_text())
            # default noon if time missing
            tm = "12:00"
            if tnode:
                m = re.search(r"(\d{1,2}:\d{2})", str(tnode))
                if m: tm = m.group(1)
            try:
                start = dateparser.parse(f"{dt_date.date()} {tm}", dayfirst=True).replace(tzinfo=tzinfo)
            except Exception:
                continue
            events.append(Event(
                start=start,
                end=start + timedelta(hours=1),
                title=title,
                description=f"БНБ – {dt_date.strftime('%d %B %Y')} {tm}",
                url=base_url,
                all_day=False
            ))

    # Dedup by (start,title)
    key = set()
    uniq: List[Event] = []
    for e in events:
        k = (e.start.isoformat(), e.title)
        if k not in key:
            key.add(k); uniq.append(e)
    uniq.sort(key=lambda e: (e.start, e.title))
    return uniq

def scrape() -> List[Event]:
    html = fetch(ROOT)
    return parse(html, ROOT)

if __name__ == "__main__":
    evs = scrape()
    print(f"BNB events: {len(evs)}")
    for e in evs[:5]:
        print(e.start.isoformat(), e.title)
