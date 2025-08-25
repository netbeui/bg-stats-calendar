# src/build_ics.py
"""
Build ICS files for NSI + BNB and publish to ./dist
Usage:
  python -m src.build_ics
"""
from __future__ import annotations
import os
from pathlib import Path
from .nsi import scrape as scrape_nsi
from .bnb import scrape as scrape_bnb
from .common import write_ics, merge_events

DIST = Path("dist")
DIST.mkdir(exist_ok=True)

def main():
    nsi_events = scrape_nsi()
    bnb_events = scrape_bnb()

    write_ics(DIST / "nsi.ics", nsi_events, "NSI releases")
    write_ics(DIST / "bnb.ics", bnb_events, "BNB statistics releases")
    all_events = merge_events(nsi_events, bnb_events)
    write_ics(DIST / "bg_stats.ics", all_events, "BG statistics (NSI + BNB)")

    print("Wrote:", [str(p) for p in DIST.glob("*.ics")])

if __name__ == "__main__":
    main()
