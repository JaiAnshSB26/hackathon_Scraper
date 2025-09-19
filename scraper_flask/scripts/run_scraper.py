"""
Runner script used by GitHub Actions (or local runs).
- Imports fetch_all_hackathons from flaskr.scraping
- Writes output to scraper_flask/data/hackathons.json
- Prints debug info to stdout (kept intentionally)

Usage: python scripts/run_scraper.py
"""
import json
import os
import sys
import traceback
from pathlib import Path

# Ensure package import works when run from repository root
root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from flaskr.scraping import fetch_all_hackathons

OUT_DIR = root / 'data'
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / 'hackathons.json'


def main():
    try:
        print("Running fetch_all_hackathons()...")
        hacks = fetch_all_hackathons()
        print(f"Fetched {len(hacks)} hackathons. Writing to {OUT_FILE}")
        with OUT_FILE.open('w', encoding='utf-8') as f:
            json.dump(hacks, f, ensure_ascii=False, indent=2)
        print('Done')
        return 0
    except Exception:
        print('Scraper failed:')
        traceback.print_exc()
        return 2


if __name__ == '__main__':
    sys.exit(main())
