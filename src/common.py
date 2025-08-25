# src/common.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Optional, List, Iterable
from dateutil import tz
import re
import uuid

SOFIA_TZID = "Europe/Sofia"

@dataclass
class Event:
    start: datetime
    end: Optional[datetime] = None
    title: str = ""
    description: str = ""
    url: str = ""
    all_day: bool = False

def ics_escape(text: str) -> str:
    return (text or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

def _format_dt(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%S")

def _format_date(d: date) -> str:
    return d.strftime("%Y%m%d")

def build_vtimezone_block() -> str:
    # Minimal VTIMEZONE for Europe/Sofia (EET/EEST). Correctness matters for Google Calendar.
    return "\r\n".join([
        "BEGIN:VTIMEZONE",
        f"TZID:{SOFIA_TZID}",
        "X-LIC-LOCATION:Europe/Sofia",
        "BEGIN:STANDARD",
        "TZOFFSETFROM:+0300",
        "TZOFFSETTO:+0200",
        "TZNAME:EET",
        "DTSTART:19701025T040000",
        "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU",
        "END:STANDARD",
        "BEGIN:DAYLIGHT",
        "TZOFFSETFROM:+0200",
        "TZOFFSETTO:+0300",
        "TZNAME:EEST",
        "DTSTART:19700329T030000",
        "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU",
        "END:DAYLIGHT",
        "END:VTIMEZONE",
    ])

def to_sofia(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz.gettz(SOFIA_TZID))
    return dt.astimezone(tz.gettz(SOFIA_TZID))

def merge_events(*lists: Iterable[Event]) -> List[Event]:
    out = [e for lst in lists for e in lst]
    out.sort(key=lambda e: (e.start, e.title))
    return out

def write_ics(path: str, events: List[Event], calname: str) -> None:
    now_utc = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    lines = []
    lines.append("BEGIN:VCALENDAR")
    lines.append("VERSION:2.0")
    lines.append("PRODID:-//BG Stats ICS//Automation//EN")
    lines.append("CALSCALE:GREGORIAN")
    lines.append("METHOD:PUBLISH")
    lines.append(f"X-WR-CALNAME:{ics_escape(calname)}")
    lines.append(f"X-WR-TIMEZONE:{SOFIA_TZID}")
    lines.append(build_vtimezone_block())

    for ev in events:
        uid = f"{uuid.uuid4()}@bg-stats-ics"
        if ev.all_day:
            dtstart = _format_date(ev.start.date())
            dtend = _format_date((ev.start.date() + timedelta(days=1)))
        else:
            start = to_sofia(ev.start)
            end = to_sofia(ev.end or (ev.start + timedelta(hours=1)))
            dtstart = _format_dt(start)
            dtend = _format_dt(end)

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now_utc}",
            f"DTSTART{';VALUE=DATE' if ev.all_day else f':TZID={SOFIA_TZID}'}:{dtstart}",
            f"DTEND{';VALUE=DATE' if ev.all_day else f':TZID={SOFIA_TZID}'}:{dtend}",
            f"SUMMARY:{ics_escape(ev.title)}",
            f"DESCRIPTION:{ics_escape(ev.description)}",
        ])
        if ev.url:
            lines.append(f"URL:{ics_escape(ev.url)}")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\r\n".join(lines))
